"""Rebuild opening graphics and the opening speaker labels."""

import argparse
import struct
from pathlib import Path

from build_expanded_dialogues import compress_lz10
from patch_frontend import BASE, Sprites, TextMasks, box, decompress, file_ids, parse_ncgr, parse_nclr
from rtz_dialogue_tool import patch_dialogue_slots

ASSETS = BASE / "extracted/nitrofs"
HEADINGS = ("Escolha o", "protagonista")
SUBTITLE = "~ Quem me chama? ~"
NAMES = {
    0x306E8: ("エミ", "Emi"), 0x30788: ("カツヤ", "Katsuya"),
    0x30720: ("ハヤト", "Hayato"), 0x30700: ("アヤ", "Aya"),
    0x30790: ("トウヤ", "Touya"), 0x30830: ("ナツミ", "Natsumi"),
    0x307F8: ("アルバ", "Alba"), 0x30770: ("ガゼル", "Gazel"),
    0x307D8: ("ラムダ", "Lambda"), 0x307E8: ("レイド", "Reid"),
    0x30838: ("アカネ", "Akane"), 0x30808: ("リプレ", "Riple"),
    0x30864: ("モナティ", "Monaty"), 0x30780: ("カノン", "Kanon"),
    0x307F0: ("ケイナ", "Keina"),
}


def selection(sprites, text):
    for label, size, region, fill, stroke, bank in (
        (HEADINGS[0], 24, box(5, 4, 165, 31), 10, (7, 1), {0}),
        (HEADINGS[1], 19, box(5, 33, 170, 53), 31, (17, 25), {16}),
    ):
        inks = text.draw(label, size, True, region, fill, stroke, left=True)
        # All eight animation cells share the original character tiles.
        sprites.paint(1, box(0, 0, 192, 56), inks, banks=bank)


def chapter_title(sprites, text, digits):
    for label, size, region, fill, stroke, bank in (
        ("Cap. 0", 14, box(1, 2, 47, 36), 15, (3,), {0}),
        ("Prólogo", 23, box(98, 3, 198, 31), 31, (18,), {16}),
    ):
        masks = digits if bank == {0} else text
        inks = masks.draw(label, size, True, region, fill, stroke)
        assert set(inks) <= {(x, y) for x, y, _, _, palette in sprites.pixels(1) if palette in bank}
        sprites.paint(1, box(0, 0, 200, 40), inks, banks=bank)


def location(sprites, text):
    count, bank_type, table = struct.unpack_from("<HHI", sprites.data, sprites.bank)
    size = 16 if bank_type == 1 else 8
    start = sprites.bank+table
    _, _, offset = struct.unpack_from("<HHI", sprites.data, start)
    for i, sprite in enumerate(sprites.cells[0]):
        if sprite["x"] == 20:
            attr = start+size*count+offset+6*i+2
            old = struct.unpack_from("<H", sprites.data, attr)[0]
            struct.pack_into("<H", sprites.data, attr, (old & ~511) | 12)
            sprite["x"] = 12
    region = box(1, 1, 95, 23)
    inks = text.draw("Caminho de casa", 13, True, region, 15, (1, 1))
    sprites.paint(0, box(0, 0, 104, 24), inks)


def chapter_location(sprites, text):
    region = box(0, 0, 96, 24)
    inks = text.draw("Caminho de casa", 13, True, box(2, 1, 94, 23), 15, (1, 1))
    # The four palette variants share the same tiles.
    sprites.paint(1, region, inks)


def speaker_plate(sprites, text, name, width, tile_limit):
    _, _, x0, y0 = sprites.layout(1)
    first = sprites.cells[1][0]
    x, y = first["x"] - x0, first["y"] - y0
    size = 17 if name == "Emi" else 15
    region = box(x + 2, y + 1, x + width - 2, y + 21)
    ink = text.draw(name, size, True, region, 239, (225, 225))
    end = sprites.start + (tile_limit << sprites.shift) * 32
    for px, py, offset, shift, bank in sprites.pixels(1):
        if offset < end:
            assert shift == bank == 0
            sprites.data[offset] = ink.get((px, py), 0)


def insert_tiles(data, pixels, extra):
    screen = data.index(b"GMIF")
    graphics = data.rfind(b"RGCN", screen, pixels)
    character = data.index(b"RAHC", graphics, pixels)
    count = struct.unpack_from("<H", data, 24)[0]
    for offset in (8, screen+4, graphics+8, character+4, character+24):
        value = struct.unpack_from("<I", data, offset)[0]
        struct.pack_into("<I", data, offset, value + len(extra))
    relative = pixels - screen - 8
    for i in range(count):
        offset = 28+8*i
        lo, hi = struct.unpack_from("<II", data, offset)
        struct.pack_into("<II", data, offset, lo+(len(extra) if lo >= relative else 0),
                         hi+(len(extra) if hi >= relative else 0))
    data[pixels:pixels] = extra


def chapter_background(data, text, opening, digits):
    data = bytearray(decompress(data))
    bpp, start, original = parse_ncgr(data)
    stride = 64 if bpp == 8 else 32
    palette = parse_nclr(data)
    scr = data.index(b"NRCS")
    width, height, _, size = struct.unpack_from("<HHII", data, scr+8)
    entries = list(struct.unpack_from(f"<{size//2}H", data, scr+20))
    assert width == 256 and len(entries) == width*height//64
    tiles = [bytes(original[i:i+stride]) for i in range(0, len(original), stride)]
    cache = {tile: i for i, tile in enumerate(tiles)}

    def read(x, y):
        item = entries[y//8*32+x//8]
        dx = 7-x%8 if item & 1024 else x%8
        dy = 7-y%8 if item & 2048 else y%8
        return tile_value(tiles[item & 1023], dx+dy*8)

    def tile_value(tile, pos):
        return tile[pos] if bpp == 8 else (tile[pos//2] >> (4*(pos%2))) & 15

    if opening:
        art = box(26, 56, 230, 109)
        subtitle = box(47, 114, 209, 132)
        title_region = box(79, 61, 227, 103)
        title_size = 28
    else:
        art = set()
        subtitle = box(52, 78, 204, 96)
    altered = {}
    if opening:
        dark = read(5, 75)
        white = max(range(256), key=lambda i: sum(palette[i*3:i*3+3]))
        copper = min(range(256), key=lambda i: sum((a-b)**2 for a,b in zip(
            palette[i*3:i*3+3], (184, 112, 64))))
        altered.update(dict.fromkeys(art, dark))
        altered.update(text.draw("Prólogo", title_size, True, title_region, white))
        altered.update(digits.draw("Cap. 0", 17, True, box(27, 65, 78, 101), copper))
    for x, y in subtitle:
        top, bottom = (114, 131) if opening else (78, 95)
        a, b = read(x, top), read(x, bottom)
        shades = range(256) if bpp == 8 else range(16)
        target = max(a, b, key=lambda i: sum(palette[i*3:i*3+3]))
        nearby = [read(xx, y) for xx in range(max(x-9, 0), min(x+10, width))]
        peak = max(nearby, key=lambda i: sum(palette[i*3:i*3+3]))
        altered[x,y] = max((target, peak), key=lambda i: sum(palette[i*3:i*3+3]))
    darkest = min(shades, key=lambda i: sum(palette[i*3:i*3+3]))
    inner = box(54, 115, 202, 131) if opening else box(55, 79, 201, 95)
    altered.update(text.draw(SUBTITLE, 10, True, inner, darkest))
    for tx, ty in {(x//8, y//8) for x,y in altered}:
        idx = ty*32+tx
        values = [altered.get((x,y), read(x,y)) for y in range(ty*8,ty*8+8)
                  for x in range(tx*8,tx*8+8)]
        packed = bytes(values if bpp == 8 else [a | b<<4 for a,b in zip(values[::2], values[1::2])])
        if packed not in cache:
            cache[packed] = len(tiles)
            tiles.append(packed)
        tile_id = cache[packed]
        assert tile_id < 1024
        struct.pack_into("<H", data, scr+20+2*idx, (entries[idx] & 0xF000) | tile_id)
    extra = b"".join(tiles[len(original)//stride:])
    if extra:
        insert_tiles(data, start+len(original), extra)
    return data


def build(source, output):
    if source.resolve() == output.resolve():
        raise ValueError("Use um caminho diferente para a ROM de saída.")
    rom = bytearray(source.read_bytes())
    assert rom[12:16] == b"YSMJ"
    ids = file_ids(rom)
    fat = struct.unpack_from("<I", rom, 0x48)[0]

    def replace(file_id, data, packed=True, in_place=False):
        payload = compress_lz10(bytes(data)) if packed else data
        if packed and decompress(payload) != data:
            raise ValueError(f"Erro LZ10 no arquivo {file_id}")
        if in_place:
            start, end = struct.unpack_from("<II", rom, fat + 8 * file_id)
            if len(payload) <= end - start:
                rom[start:end] = payload.ljust(end - start, b"\0")
                return
        rom.extend(bytes(-len(rom)%4))
        start = len(rom)
        rom.extend(payload)
        struct.pack_into("<II", rom, fat+8*file_id, start, len(rom))

    condensed = TextMasks("Arial Narrow")
    condensed.load([(HEADINGS[0],24,True),(HEADINGS[1],19,True),
                    ("Caminho de casa",13,True),("Emi",17,True),("Katsuya",15,True)])
    digits = TextMasks("Arial")
    digits.load([("Cap. 0",14,True),("Cap. 0",17,True)])
    serif = TextMasks("Georgia")
    serif.load([("Prólogo",23,True),("Prólogo",28,True),
                (SUBTITLE,10,True)])
    for name, edit, masks in (
        ("charaselect/sn0_cs_sub_title.narc", selection, condensed),
        ("chaptersub/cptsub00_000.narc", lambda sprite, masks: chapter_title(sprite, masks, digits), serif),
        ("system/ev0002_043.narc", location, condensed),
        ("chaptersub/ev00_043.narc", chapter_location, condensed),
    ):
        sprite = Sprites((ASSETS/name).read_bytes())
        edit(sprite, masks)
        replace(ids[name], sprite.data, in_place=name.startswith("system/"))
    for name, opening in (("chapter/cpt000.narc", True), ("chaptersub/cptsub00_000bg.narc", False)):
        replace(ids[name], chapter_background((ASSETS/name).read_bytes(), serif, opening, digits))

    for name, label, width, tile_limit in (
        ("evface/ec0099.narc", "Emi", 40, 5),
        ("evface/ec0098.narc", "Katsuya", 64, 6),
    ):
        sprite = Sprites((ASSETS/name).read_bytes())
        speaker_plate(sprite, condensed, label, width, tile_limit)
        replace(ids[name], sprite.data, in_place=True)

    overlay_entry = struct.unpack_from("<I",rom,0x50)[0]+2*32
    overlay_id, _, size, _, _, _, file_id, flags = struct.unpack_from("<8I",rom,overlay_entry)
    assert overlay_id == 2 and flags & 0x01000000
    overlay = bytearray((BASE/"extracted/bin/overlays_arm9/overlay_0002.bin").read_bytes())
    assert len(overlay) == size
    for offset,(japanese,latin) in NAMES.items():
        old = japanese.encode("cp932")+b"\0"
        limit = (len(old)+3)&~3
        new = latin.encode("ascii")+b"\0"
        assert len(new)<=limit and overlay[offset:offset+limit]==old.ljust(limit,b"\0")
        overlay[offset:offset+limit] = new.ljust(limit,b"\0")
    replace(file_id,overlay,packed=False)
    struct.pack_into("<I",rom,overlay_entry+28, (flags & 0xFE000000) | len(overlay))

    for scene, batch, expected in (("scn000a", 8, 481), ("scn000b", 9, 297)):
        relative = f"scnrts/{scene}.rtz"
        original = (BASE/"extracted/rtz_unpacked"/relative).read_bytes()
        markdown = BASE/"ARQUIVOS md"/f"{batch:02}-dialogos-{scene}.md"
        script, count, pending = patch_dialogue_slots(markdown, original, expand=True)
        assert not pending and count == expected
        replace(ids[relative], script)
    struct.pack_into("<I",rom,0x80,len(rom))
    crc=0xFFFF
    for byte in rom[:0x15E]:
        crc ^= byte
        for _ in range(8):
            crc=(crc>>1) ^ (0xA001 if crc&1 else 0)
    struct.pack_into("<H",rom,0x15E,crc)
    output.write_bytes(rom)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source",type=Path)
    parser.add_argument("output",type=Path)
    build(**vars(parser.parse_args()))
