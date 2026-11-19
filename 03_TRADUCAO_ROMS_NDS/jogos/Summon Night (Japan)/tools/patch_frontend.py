"""Inspect and patch Summon Night's indexed UI sprites."""

import struct
import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

from oam_ncer_tool import parse_ncer, parse_ncgr, parse_nclr
from patch_nftr_accents import PTBR_ACCENTS

BASE = Path(__file__).resolve().parents[1]


def decompress(data):
    output = bytearray()
    size = int.from_bytes(data[1:4], "little")
    cursor = 4
    while len(output) < size:
        flags = data[cursor]
        cursor += 1
        for mask in (128, 64, 32, 16, 8, 4, 2, 1):
            if len(output) >= size:
                break
            first = data[cursor]
            cursor += 1
            if flags & mask:
                distance = ((first & 15) << 8) + data[cursor] + 1
                cursor += 1
                for _ in range((first >> 4) + 3):
                    output.append(output[-distance])
            else:
                output.append(first)
    return output


def literal_lz10(data):
    return b"\x10" + len(data).to_bytes(3, "little") + b"".join(
        b"\0" + data[i:i + 8] for i in range(0, len(data), 8)
    )


class Sprites:
    def __init__(self, data):
        self.data = decompress(data) if data[0] == 16 else bytearray(data)
        assert self.data[:4] == b"NARC"
        count = struct.unpack_from("<H", self.data, 24)[0]
        start = self.data.index(b"GMIF", 28 + count * 8) + 8
        members = {}
        for i in range(count):
            lo, hi = struct.unpack_from("<II", self.data, 28 + i * 8)
            members[bytes(self.data[start + lo:start + lo + 4])] = (start + lo, start + hi)
        ncgr, end = members[b"RGCN"]
        self.bpp, offset, pixels = parse_ncgr(self.data[ncgr:end])
        self.start = ncgr + offset
        self.linear = bool(struct.unpack_from("<I", self.data, self.start - 12)[0] & 1)
        self.length = len(pixels)
        lo, hi = members[b"RECN"]
        self.bank = self.data.index(b"KBEC", lo, hi) + 8
        self.shift, self.cells = parse_ncer(self.data[lo:hi])
        lo, hi = members[b"RLCN"]
        self.palette = parse_nclr(self.data[lo:hi])

    def layout(self, cell):
        oams = self.cells[cell]
        x0 = min(o["x"] for o in oams)
        y0 = min(o["y"] for o in oams)
        width = max(o["x"] + o["w"] for o in oams) - x0
        height = max(o["y"] + o["h"] for o in oams) - y0
        return width, height, x0, y0

    def pixels(self, cell):
        _, _, x0, y0 = self.layout(cell)
        for obj in reversed(self.cells[cell]):
            base = (obj["tile"] << self.shift) * 32
            for y in range(obj["h"]):
                for x in range(obj["w"]):
                    tile = y // 8 * (obj["w"] // 8) + x // 8
                    local = y * obj["w"] + x if self.linear else tile * 64 + y % 8 * 8 + x % 8
                    pixel = (base * 8 // self.bpp) + local
                    offset = pixel * self.bpp // 8
                    if offset >= self.length:
                        continue
                    dx = obj["w"] - 1 - x if obj["h_flip"] else x
                    dy = obj["h"] - 1 - y if obj["v_flip"] else y
                    shift = (pixel % 2) * 4 if self.bpp == 4 else 0
                    bank = obj["pal"] * 16 if self.bpp == 4 else 0
                    yield obj["x"] - x0 + dx, obj["y"] - y0 + dy, self.start + offset, shift, bank

    def render(self, cell):
        mask = (1 << self.bpp) - 1
        result = {}
        for x, y, offset, shift, bank in self.pixels(cell):
            index = (self.data[offset] >> shift) & mask
            if index:
                result[x, y] = index + bank
        return result

    def paint(self, cell, region, indexes, background=0, banks=None):
        mask = (1 << self.bpp) - 1
        for x, y, offset, shift, bank in self.pixels(cell):
            if (x, y) in region and (banks is None or bank in banks):
                index = indexes.get((x, y), background) & mask
                self.data[offset] = (self.data[offset] & ~(mask << shift)) | index << shift

    def swap_cells(self, first, second):
        _, bank_type, table = struct.unpack_from("<HHI", self.data, self.bank)
        size = 16 if bank_type == 1 else 8
        a, b = (self.bank + table + size * i for i in (first, second))
        self.data[a:a+size], self.data[b:b+size] = self.data[b:b+size], self.data[a:a+size]
        self.cells[first], self.cells[second] = self.cells[second], self.cells[first]

    def reserve_confirmation_tiles(self):
        count = struct.unpack_from("<H", self.data, 24)[0]
        image = self.data.index(b"GMIF", 28 + count * 8)
        ncgr = self.data.rfind(b"RGCN", image + 8, self.start)
        character = self.data.index(b"RAHC", ncgr, self.start)
        first_tile = self.length // 128
        extra = 256
        insertion = self.start + self.length
        for offset in (8, image + 4, ncgr + 8, character + 4, character + 24):
            value = struct.unpack_from("<I", self.data, offset)[0]
            struct.pack_into("<I", self.data, offset, value + extra)
        relative = insertion - image - 8
        for index in range(count):
            offset = 28 + index * 8
            lo, hi = struct.unpack_from("<II", self.data, offset)
            if lo >= relative:
                lo += extra
            if hi >= relative:
                hi += extra
            struct.pack_into("<II", self.data, offset, lo, hi)
        self.data[insertion:insertion] = bytes(extra)
        self.length += extra
        return first_tile

    def reframe_confirmation_no(self, cell, tile):
        count, bank_type, table = struct.unpack_from("<HHI", self.data, self.bank)
        size = 16 if bank_type == 1 else 8
        entries = self.bank + table
        _, _, relative = struct.unpack_from("<HHI", self.data, entries + size * cell)
        start = entries + size * count + relative
        for i, obj in enumerate(self.cells[cell]):
            if obj["pal"] not in (12, 14):
                continue
            pos = start + 6 * i
            a0, a1, a2 = struct.unpack_from("<HHH", self.data, pos)
            # All original text objects now reference the same 32×16 label.
            struct.pack_into("<HHH", self.data, pos,
                             (a0 & 0x3F00) | 0x4000 | 248,
                             (a1 & 0x3E00) | 0x8000 | 496,
                             (a2 & 0xFC00) | tile)
            obj.update(x=-16, y=-8, w=32, h=16, tile=tile)


def box(x0, y0, x1, y1):
    return {(x, y) for x in range(x0, x1) for y in range(y0, y1)}


class TextMasks:
    def __init__(self, family="Arial"):
        self.items = {}
        self.family = family

    def load(self, requests):
        requests = list(dict.fromkeys(requests))
        payload = [dict(text=text, size=size, bold=bold, family=self.family) for text, size, bold in requests]
        script = Path(__file__).with_name("render_ui_masks.ps1")
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-File", str(script)],
            input=json.dumps(payload).encode("ascii"), capture_output=True, check=True,
        )
        for key, item in zip(requests, json.loads(result.stdout), strict=True):
            points = {(p % 280, p // 280) for p in item["pixels"]}
            self.items[key] = points

    def draw(self, text, size, bold, region, color, border=(), left=False):
        points = self.items[text, size, bold]
        x0, y0 = map(min, zip(*points))
        x1, y1 = map(max, zip(*points))
        rx0, ry0 = map(min, zip(*region))
        rx1, ry1 = map(max, zip(*region))
        assert x1 - x0 + 1 <= rx1 - rx0 + 1 and y1 - y0 + 1 <= ry1 - ry0 + 1, text
        dx = rx0 - x0 if left else (rx0 + rx1 - x0 - x1) // 2
        dy = (ry0 + ry1 - y0 - y1) // 2
        points = {(x+dx, y+dy) for x, y in points}
        inks = {}
        for radius, index in reversed(list(enumerate(border, 1))):
            for x, y in points:
                for bx in range(-radius, radius + 1):
                    for by in range(-radius, radius + 1):
                        if abs(bx) + abs(by) <= radius + 1:
                            inks[x+bx, y+by] = index
        inks.update(dict.fromkeys(points, color))
        return inks


PROMPT = "Toque na tela de baixo"
MENU = ("Novo jogo", "Continuar", "Retomar", "Opções")
INFORMATION = "INFORMAÇÃO"
CONFIRMATION = "CONFIRME"
TABS = ("Letras", "Katakana", "Hiragana", "Kanji")
BUTTONS = ("Padrão", "Apagar", "OK")
OPTION_ROWS = ("Música", "Efeitos", "Veloc. do texto", "Controle",
               "Direção do", "cursor")
OPTION_VALUES = ("Mudo", "Baixo", "Médio", "Alto", "Normal", "Rápido", "Tipo A", "Tipo B")
DESCRIPTIONS = (
    ("Enfrenta desafios", "com coragem. Age",
     "por impulso, mas", "supera as crises", "com muita garra."),
    ("Realista, encara",
     "o mundo como ele é.",
     "Acredita no destino,", "mas não se entrega", "sem lutar."),
    ("Vê o futuro com", "alegria. Gosta de", "cuidar dos outros,",
     "mas às vezes se", "intromete demais."),
    ("Calma e romântica,",
     "Gosta de ficar só", "com os pensamentos", "e evita se destacar."),
)
KEYS = (
    "ABCDEFGHIJKLMNO",
    "PQRSTUVWXYZabcd",
    "efghijklmnopqrs",
    "tuvwxyzÁÀÂÃÇÉÊÍ",
    "ÓÔÕÚáàâãçéêíóôõ",
    "ú1234567890-.'!",
    "?              ",
)
ACCENTS = {character: code.to_bytes(2, "big") for character, code, _, _ in PTBR_ACCENTS}


def title_sprites(sprites, text, alternate):
    groups = ([0, 1], [9, 10], [11, 12], [13, 14], [15, 16]) if not alternate else (
        range(1, 8), range(8, 15), range(15, 22), (*range(22, 29), 36, 37), range(29, 36)
    )
    for label, cells in zip((PROMPT, *MENU), groups, strict=True):
        for cell in cells:
            width, height, *_ = sprites.layout(cell)
            old = sprites.render(cell)
            if alternate:
                fill = Counter(index for index in old.values()
                               if max(sprites.palette[index*3:index*3+3]) < 215).most_common(1)[0][0]
            else:
                fill = 131 if cell % 2 == (0 if cell < 2 else 1) else 1
            region = box(0, 0, width, height)
            inks = text.draw(label, 16, True, region, fill, (254, 42))
            sprites.paint(cell, region, inks)


def information_header(sprites, text):
    inks = text.draw(INFORMATION, 7, True, box(5, 2, 82, 10), 5, (1,), left=True)
    sprites.paint(1, box(4, 2, 84, 10), inks, banks={224})


def confirmation_dialog(sprites, text):
    region = box(6, 0, 70, 8)
    header = text.draw(CONFIRMATION, 8, True, box(8, 0, 68, 8), 12, (13,), left=True)
    sprites.paint(2, region, header, banks={64})
    region = box(12, 4, 44, 20)
    yes = text.draw("Sim", 12, True, box(14, 5, 42, 19), 1, (4,))
    sprites.paint(5, region, yes, banks={192})
    tile = sprites.reserve_confirmation_tiles()
    for cell in (8, 9, 10):
        sprites.reframe_confirmation_no(cell, tile)
    region = box(12, 4, 44, 20)
    no = text.draw("Não", 12, True, box(14, 5, 42, 19), 1, (4,))
    sprites.paint(8, region, no, banks={192})


def character_panel(sprites, text, character):
    bank = 16 * (character + 2)
    # Keep the original panel silhouette, decorative tips and color scheme.
    region = {
        (x, y) for (x, y), index in sprites.render(1).items()
        if 3 <= y < 98 and (x < 116 or index < bank + 14)
    }
    lines = DESCRIPTIONS[character]
    top = 49 - len(lines) * 7
    inks = {}
    for row, line in enumerate(lines):
        y = top + 14 * row
        inks.update(text.draw(line, 11, False, box(5, y, 115, y+13), bank+1, left=True))
    sprites.paint(1, region, inks, bank+14)


def character_buttons(sprites, text):
    for cell, label in ((5, "OK"), (6, "OK"), (7, "Voltar"), (8, "Voltar")):
        region = box(0, 0, 40, 24)
        color = 12 if cell in (5, 7) else 4
        inks = text.draw(label, 11, True, region, color, (10, 1))
        sprites.paint(cell, region, inks)


def input_buttons(sprites, text):
    for cell in range(10, 18):
        label = TABS[(cell - 10) // 2]
        region = box(7, 2, 57, 13)
        inks = text.draw(label, 10, True, box(7, 3, 57, 12), 9, (12,))
        sprites.paint(cell, region, inks, 13)
        sprites.paint(cell, box(7, 13, 57, 14), {}, 15)
    for cell in range(22, 34):
        label = BUTTONS[(cell - 22) // 4]
        if label == "Apagar":
            shift = 8 if cell == 28 else 0
            y = 1 if cell == 28 else 0
            region = box(23 + shift, 5 + y, 55 + shift, 21 + y)
            inks = text.draw(label, 9, True, region, 1)
            sprites.paint(cell, region, inks, banks={192, 208, 224})
            continue
        x0 = 32 if cell in (24, 28, 32) else 24
        x1 = x0 + (54 if cell < 26 else 34)
        y0 = 5 if cell in (24, 28, 32) else 4
        region = box(x0, y0, x1, y0+15)
        inks = text.draw(label, 9, True, region, 1, (4,))
        sprites.paint(cell, region, inks, banks={192, 208, 224})


def option_menu(sprites, text):
    region = box(8, 0, 56, 8)
    header = text.draw("OPÇÕES", 7, True, box(9, 0, 54, 8), 12, (13,), left=True)
    sprites.paint(3, region, header, banks={112})
    for cell, label in zip(range(4, 12, 2), OPTION_ROWS[:4], strict=True):
        width, height, *_ = sprites.layout(cell)
        region = box(0, 0, width, height)
        inks = text.draw(label, 10, True, box(0, 1, width, 15), 1, (4,), left=True)
        sprites.paint(cell, region, inks)
    inks = {}
    for row, label in enumerate(OPTION_ROWS[4:]):
        inks.update(text.draw(label, 10, True, box(0, 2 + row*13, 64, 14 + row*13),
                               1, (4,), left=True))
    sprites.paint(12, box(0, 0, 64, 32), inks)
    for cell, label in zip(range(14, 30, 2), OPTION_VALUES, strict=True):
        width = 36 if cell < 22 else 48
        region = box(3, 2, width - 3, 13)
        inks = text.draw(label, 9, True, box(4, 2, width - 4, 13), 10, (13,))
        for x in range(3, width - 3):
            inks.setdefault((x, 2), 15)
        sprites.paint(cell, region, inks, 14)

    region = box(6, 7, 26, 17)
    inks = text.draw("Sair", 9, True, region, 12)
    sprites.paint(49, region, inks, 7)


def keyboard(sprites, text):
    cell = 3
    region = box(0, 0, 256, 112)
    inks = {}
    for y, row in enumerate(KEYS):
        for x, key in enumerate(row):
            if key == " ":
                continue
            left = 11 + 15*x + 5*(x//5)
            top = 5 + 15*y
            inks.update(text.draw(key, 12, False, box(left, top, left+12, top+14), 2))
    sprites.paint(cell, region, inks)
    sprites.swap_cells(1, 3)


def collect_masks():
    requests = [(s, 16, True) for s in (PROMPT, *MENU)]
    requests.append((INFORMATION, 7, True))
    requests += [(CONFIRMATION, 8, True), ("Sim", 12, True), ("Não", 12, True)]
    requests += [(s, 11, False) for lines in DESCRIPTIONS for s in lines]
    requests += [(s, 11, True) for s in ("Voltar", "OK")]
    requests += [(s, 10, True) for s in TABS]
    requests += [(s, 9, True) for s in BUTTONS]
    requests += [(s, 10, True) for s in OPTION_ROWS]
    requests += [(s, 9, True) for s in (*OPTION_VALUES, "Sair")]
    requests.append(("OPÇÕES", 7, True))
    requests += [(key, 12, False) for row in KEYS for key in row if key != " "]
    masks = TextMasks()
    masks.load(requests)
    return masks


def file_ids(rom):
    table = struct.unpack_from("<I", rom, 0x40)[0]
    ids = {}

    def walk(directory, prefix):
        relative, file_id, _ = struct.unpack_from("<IHH", rom, table + 8*(directory & 0xFFF))
        index = table + relative
        while length := rom[index]:
            index += 1
            name = prefix + bytes(rom[index:index + (length & 127)]).decode("ascii")
            index += length & 127
            if length & 128:
                child = struct.unpack_from("<H", rom, index)[0]
                index += 2
                walk(child, name + "/")
            else:
                ids[name] = file_id
                file_id += 1

    walk(0xF000, "")
    return ids


def patch_string(data, offset, old, new, capacity):
    assert data[offset:offset+len(old)+1] == old + b"\0", hex(offset)
    assert len(new) < capacity, (offset, new)
    data[offset:offset+capacity] = new.ljust(capacity, b"\0")


def fullwidth(text):
    return "".join(chr(ord(c) + 0xFEE0) for c in text).encode("cp932")


def game_text(text):
    return b"".join(ACCENTS[c] if c in ACCENTS else c.encode("ascii") for c in text)


def patch_arm9(arm):
    kana_ptr, kata_ptr, latin_ptr = struct.unpack_from("<III", arm, 0xC5F58)
    assert (kana_ptr, kata_ptr, latin_ptr) == (0x020C608C, 0x020C6160, 0x020C6234)
    struct.pack_into("<III", arm, 0xC5F58, latin_ptr, kata_ptr, kana_ptr)
    assert all(len(row) == 15 for row in KEYS)
    keyboard_codes = b"".join(
        ACCENTS[c] if c in ACCENTS else (fullwidth(c) if c != " " else b"\x81\x40")
        for c in "".join(KEYS)
    )
    assert arm[0xC6234:0xC623E] == fullwidth("ABCDE")
    assert arm[0xC6306:0xC6308] == b"\0\0"
    arm[0xC6234:0xC6306] = keyboard_codes
    patch_string(arm, 0xC5EFC, fullwidth("TOHYA"), fullwidth("TOUYA"), 12)


def patch_overlay(overlay):
    for offset, source, translated, capacity in (
        (0x5414, "各種設定の変更を行います", "Altere as configurações.", 28),
        (0x5430, "ゲームを続きからプレイします", "Carregue um jogo salvo.", 28),
        (0x5490, "物語の最初からゲームをプレイします", "Comece a história do início.", 36),
        (0x54B4, "中断セーブしたところからプレイします", "Retome o jogo interrompido.", 36),
    ):
        patch_string(overlay, offset, source.encode("cp932"), game_text(translated), capacity)
    for offset, source, name, capacity in (
        (0x5778, "アヤ", "AYA", 8),
        (0x5788, "トウヤ", "TOUYA", 8),
        (0x5790, "ハヤト", "HAYATO", 8),
        (0x5798, "ナツミ", "NATUMI", 8),
    ):
        old = source.encode("cp932")
        new = fullwidth(name)
        if len(new) < capacity:
            patch_string(overlay, offset, old, new, capacity)
        else:
            # The original long Latin presets already live in ARM9.
            targets = {"TOUYA": 0x020C5EFC, "HAYATO": 0x020C5F20, "NATUMI": 0x020C5F30}
            pointer = struct.pack("<I", 0x02179740 + offset)
            locations = [i for i in range(0, len(overlay)-3, 4) if overlay[i:i+4] == pointer]
            assert locations, name
            for location in locations:
                struct.pack_into("<I", overlay, location, targets[name])


def build(source, output, repair_prologue=False):
    rom = bytearray(source.read_bytes())
    assert rom[12:16] == b"YSMJ"
    ids = file_ids(rom)
    fat = struct.unpack_from("<I", rom, 0x48)[0]
    arm_offset, _, _, arm_size = struct.unpack_from("<IIII", rom, 0x20)
    arm = rom[arm_offset:arm_offset+arm_size]
    patch_arm9(arm)
    rom[arm_offset:arm_offset+arm_size] = arm

    def replace(file_id, data):
        rom.extend(bytes(-len(rom) % 4))
        start = len(rom)
        rom.extend(data)
        struct.pack_into("<II", rom, fat + 8*file_id, start, len(rom))

    table = struct.unpack_from("<I", rom, 0x50)[0]
    file_id, flags = struct.unpack_from("<II", rom, table + 24)
    overlay = bytearray((BASE / "extracted/bin/overlays_arm9/overlay_0000.bin").read_bytes())
    assert len(overlay) == struct.unpack_from("<I", rom, table + 8)[0]
    patch_overlay(overlay)
    replace(file_id, overlay)
    struct.pack_into("<I", rom, table + 28, (flags & 0xFE000000) | len(overlay))

    masks = collect_masks()
    changes = {
        "title/ti000_main00": lambda sprite: title_sprites(sprite, masks, False),
        "title/ti0_sp_sub0001": lambda sprite: title_sprites(sprite, masks, True),
        "system/ev0011": lambda sprite: information_header(sprite, masks),
        "system/save0004": lambda sprite: confirmation_dialog(sprite, masks),
        "system/save0005": lambda sprite: confirmation_dialog(sprite, masks),
        "charaselect/sn0_cs_main_bot": lambda sprite: character_buttons(sprite, masks),
        "input/input_sp_main0000": lambda sprite: input_buttons(sprite, masks),
        "input/input_sp_main0001": lambda sprite: keyboard(sprite, masks),
        "option/option_sp_main0000": lambda sprite: option_menu(sprite, masks),
        "option/option_sp_sub0000": lambda sprite: option_menu(sprite, masks),
    }
    for i in range(4):
        changes[f"charaselect/sn0_cs_sub_pane{i:02}"] = (
            lambda sprite, character=i: character_panel(sprite, masks, character)
        )
    for name, edit in changes.items():
        relative = name + ".narc"
        sprites = Sprites((BASE / "extracted/nitrofs" / relative).read_bytes())
        edit(sprites)
        data = literal_lz10(sprites.data)
        assert decompress(data) == sprites.data
        replace(ids[relative], data)
    if repair_prologue:
        from rtz_dialogue_tool import patch_dialogue_slots

        for scene, markdown in (("scn000a", "08"), ("scn000b", "09")):
            relative = f"scnrts/{scene}.rtz"
            original = (BASE / "extracted/rtz_unpacked" / relative).read_bytes()
            path = BASE / "ARQUIVOS md" / f"{markdown}-dialogos-{scene}.md"
            patched, count, deferred = patch_dialogue_slots(path, original)
            assert len(patched) == len(original)
            replace(ids[relative], literal_lz10(patched))
            print(f"{scene}: {count} falas inseridas, {len(deferred)} no original")
    struct.pack_into("<I", rom, 0x80, len(rom))
    crc = 0xFFFF
    for byte in rom[:0x15E]:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    struct.pack_into("<H", rom, 0x15E, crc)
    output.write_bytes(rom)
    print(output)


def sheet(archives, path):
    rows = []
    for name in archives:
        sprites = Sprites((BASE / "extracted/nitrofs" / (name + ".narc")).read_bytes())
        for i, objects in enumerate(sprites.cells):
            if objects:
                width, height, *_ = sprites.layout(i)
                rows.append((name, i, width, height, sprites.render(i), sprites.palette))
    width = 3 * 256
    height = sum(max(row[3] for row in rows[i:i+3]) for i in range(0, len(rows), 3))
    canvas = bytearray(bytes((99, 122, 130)) * width * height)
    y0 = 0
    for start in range(0, len(rows), 3):
        for col, (name, i, w, h, pixels, palette) in enumerate(rows[start:start+3]):
            print(name, i, col * 256, y0, w, h)
            for (x, y), index in pixels.items():
                if x >= 256:
                    continue
                ptr = ((height - 1 - y0 - y) * width + col * 256 + x) * 3
                canvas[ptr:ptr+3] = bytes(palette[index*3:index*3+3][::-1])
        y0 += max(row[3] for row in rows[start:start+3])
    header = struct.pack("<2sIHHI", b"BM", 54 + len(canvas), 0, 0, 54)
    header += struct.pack("<IiiHHIIiiII", 40, width, height, 1, 24, 0, len(canvas), 0, 0, 0, 0)
    path.write_bytes(header + canvas)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("archives", nargs="*")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--repair-prologue", action="store_true")
    options = parser.parse_args()
    if options.source:
        build(options.source, options.path, options.repair_prologue)
    else:
        sheet(options.archives, options.path)
