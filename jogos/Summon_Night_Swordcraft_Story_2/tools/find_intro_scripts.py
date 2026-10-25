import struct
from pathlib import Path
import sys

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
rom = rom_path.read_bytes()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_extractor import decompress_gba_lz77, parse_archive_table
from extract_dialogues_to_md import decode_sjis_u16

entries = parse_archive_table(rom, 0x08ABA81C, 0x08C7F5FC)
print(f"Scanning {len(entries)} Archive 2 scripts for intro dialogue...")

keywords = ['Blaire', 'wake up', 'apprentice', 'Craftlord', 'orphan', 'village', 'Colat', 'ruins']
intro_scripts = []

for ent in entries:
    raw = rom[ent['file_offset'] : ent['file_offset'] + ent['compressed_size']]
    decomp = None
    if ent['is_lz77']:
        res = decompress_gba_lz77(raw)
        if res: decomp = res[0]
    else:
        decomp = raw
    if not decomp or not decomp.startswith(b'PSI3'):
        continue

    # scan for strings
    p = 16
    n = len(decomp)
    script_texts = []
    while p + 1 < n:
        op = struct.unpack_from('<H', decomp, p)[0]
        if op in (0x0306, 0x0361, 0x0310, 0x030D):
            text, next_p = decode_sjis_u16(decomp, p + 2)
            if any(k.lower() in text.lower() for k in keywords):
                script_texts.append((hex(p), text))
            p = next_p
        else:
            p += 2
    if script_texts:
        intro_scripts.append((ent['index'], script_texts))

print(f"Found {len(intro_scripts)} scripts matching intro keywords. First 10:")
for s_id, texts in intro_scripts[:10]:
    print(f"\nScript {s_id:04d} ({len(texts)} matches):")
    for off, t in texts[:3]:
        print(f"  {off}: {t}")
