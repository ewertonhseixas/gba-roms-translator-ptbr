"""Build a test ROM with variable-length RTZ dialogue operands."""

import argparse
import re
import struct
from collections import Counter
from pathlib import Path

from patch_frontend import BASE, decompress, file_ids
from rtz_dialogue_tool import encode_ptbr_sjis, patch_dialogue_slots
from translation_markdown import batch_lines, plain_translation, split_md_row


def expand_arm9_system_strings(rom):
    """Use verified alignment padding after directly referenced strings."""
    arm_offset, _, address, size = struct.unpack_from("<4I", rom, 0x20)
    original = (BASE / "extracted/bin/arm9_dec.bin").read_bytes()
    arm = bytearray(rom[arm_offset:arm_offset+size])
    if len(original) != size:
        raise ValueError("ARM9 de tamanho diferente da extração usada nas traduções.")
    refs = set(struct.unpack_from("<I", arm, i)[0] for i in range(0, len(arm)-3, 4))
    row = re.compile(r"arm9_dec\.bin `0x([\dA-Fa-f]+)` \((\d+)B\)")
    format_code = re.compile(rb"%(?:%|[-+ #0]*\d*(?:\.\d+)?[hlL]*[diouxXeEfFgGcsnp])")
    count = 0
    for line in batch_lines(BASE / "ARQUIVOS md/03-mensagens-do-sistema.md"):
        if not line.startswith("|"):
            continue
        cells = split_md_row(line)
        match = row.fullmatch(cells[0])
        if len(cells) != 5 or not match:
            continue
        start, length = int(match[1], 16), int(match[2])
        end = start + length
        aligned_end = (end + 4) & ~3
        if (
            start < 0x097000 or start % 4 or aligned_end > len(arm)
            or address + start not in refs
            or any(address + pos in refs for pos in range(start+1, aligned_end))
            or b"\0" in original[start:end]
            or any(original[end:aligned_end]) or any(arm[end:aligned_end])
        ):
            continue
        text = plain_translation(cells[3]).replace("<br>", "\n")
        try:
            if len(text.encode("cp1252")) <= length:
                continue
        except UnicodeEncodeError:
            pass
        try:
            encoded = encode_ptbr_sjis(text)
        except UnicodeEncodeError:
            continue
        if not length < len(encoded) < aligned_end - start:
            continue
        if format_code.findall(original[start:end]) != format_code.findall(encoded):
            continue
        arm[start:aligned_end] = encoded.ljust(aligned_end-start, b"\0")
        count += 1
    rom[arm_offset:arm_offset+size] = arm
    return count


def compress_lz10(data):
    packed = bytearray(b"\x10" + len(data).to_bytes(3, "little"))
    pos = 0
    while pos < len(data):
        group = len(packed)
        packed.append(0)
        for bit in range(7, -1, -1):
            if pos == len(data):
                break
            limit = min(18, len(data) - pos)
            length = 0
            previous = pos
            if limit >= 3:
                prefix = data[pos:pos+3]
                within_window = max(0, pos - 4096)
                for _ in range(24):
                    previous = data.rfind(prefix, within_window, previous)
                    if previous < 0:
                        break
                    match = 3
                    while match < limit and data[previous+match] == data[pos+match]:
                        match += 1
                    if match > length:
                        length, distance = match, pos - previous
                    if length == limit:
                        break
                    previous += 2
            if length >= 3:
                packed[group] |= 1 << bit
                packed.extend((((length - 3) << 12) | (distance - 1)).to_bytes(2, "big"))
                pos += length
            else:
                packed.append(data[pos])
                pos += 1
    return bytes(packed)


def build(source, output, scenes, *, system_padding=False, graphics=None):
    if source.resolve() == output.resolve():
        raise ValueError("A ROM de teste deve ter um caminho diferente da ROM de origem.")
    rom = bytearray(source.read_bytes())
    if rom[12:16] != b"YSMJ":
        raise ValueError("A ROM de origem não é Summon Night YSMJ.")
    ids = file_ids(rom)
    fat_offset = struct.unpack_from("<I", rom, 0x48)[0]
    patched_ids = set()
    counts = Counter()
    if system_padding:
        counts["textos_de_sistema_expandidos"] = expand_arm9_system_strings(rom)
    for markdown in sorted((BASE / "ARQUIVOS md").glob("*dialogos-scn*.md")):
        match = re.fullmatch(r"\d+-dialogos-(scn\w+)\.md", markdown.name)
        if not match or (scenes and match[1] not in scenes):
            continue
        scene = match[1]
        relative = f"scnrts/{scene}.rtz"
        original = (BASE / "extracted/rtz_unpacked" / relative).read_bytes()
        packed_original = (BASE / "extracted/nitrofs" / relative).read_bytes()
        if decompress(packed_original) != original:
            raise ValueError(f"Extração original inconsistente: {relative}")
        script, translated, pending = patch_dialogue_slots(markdown, original, expand=True)
        compressed = compress_lz10(script)
        if decompress(compressed) != script:
            raise ValueError(f"Falha na verificação LZ10: {relative}")
        rom.extend(bytes(-len(rom) % 4))
        start = len(rom)
        rom.extend(compressed)
        file_id = ids[relative]
        struct.pack_into("<II", rom, fat_offset + 8 * file_id, start, len(rom))
        patched_ids.add(file_id)
        counts["roteiros"] += 1
        counts["traduzidos"] += translated
        counts["pendentes"] += len(pending)
        print(f"{scene}: {translated} falas inseridas, {len(pending)} pendentes")
    if not patched_ids or (scenes and len(patched_ids) != len(scenes)):
        raise ValueError("Uma ou mais cenas solicitadas não foram encontradas.")

    if graphics is not None:
        graphics(rom)
    struct.pack_into("<I", rom, 0x80, len(rom))
    crc = 0xFFFF
    for byte in rom[:0x15E]:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
    struct.pack_into("<H", rom, 0x15E, crc)
    with output.open("wb") as rom_file:
        rom_file.write(rom)
    print(f"{output}: {dict(counts)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--scene", action="append", default=[])
    parser.add_argument("--system-padding", action="store_true")
    args = parser.parse_args()
    build(args.source, args.output, set(args.scene), system_padding=args.system_padding)
