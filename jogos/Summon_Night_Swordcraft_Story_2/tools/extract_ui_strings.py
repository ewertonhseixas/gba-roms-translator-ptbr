import struct
from pathlib import Path

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
rom = rom_path.read_bytes()

# Build map of all 32-bit pointers pointing into 0x0808E000..0x08095000
ptr_map = {}
for off in range(0, len(rom) - 4, 4):
    val = struct.unpack_from('<I', rom, off)[0]
    if 0x0808E000 <= val < 0x08095000:
        if val not in ptr_map:
            ptr_map[val] = []
        ptr_map[val].append(0x08000000 + off)

print(f"Total pointers found pointing to 0x0808E000..0x08095000: {len(ptr_map)} unique targets")

def decode_sjis_at(off):
    chars = []
    p = off
    while p + 1 < len(rom):
        w = struct.unpack_from('>H', rom, p)[0]
        p += 2
        if w == 0: break
        elif 0x8260 <= w <= 0x8279: chars.append(chr(ord('A') + w - 0x8260))
        elif 0x8281 <= w <= 0x829A: chars.append(chr(ord('a') + w - 0x8281))
        elif 0x824F <= w <= 0x8258: chars.append(chr(ord('0') + w - 0x824F))
        elif w == 0x8140: chars.append(' ')
        elif w == 0x8143: chars.append(',')
        elif w == 0x8144: chars.append('.')
        elif w == 0x8148: chars.append('?')
        elif w == 0x8149: chars.append('!')
        elif w == 0x8166: chars.append("'")
        elif w == 0x8168: chars.append('"')
        elif w == 0x8163: chars.append('…')
        elif w == 0x817C: chars.append('-')
        elif w == 0x815E: chars.append('/')
        elif w == 0x819A: chars.append('☆')
        elif w == 0x81F4: chars.append('♪')
        else:
            return None
    s = ''.join(chars).strip()
    return s if len(s) > 0 else None

ui_strings = []
for target_addr, refs in sorted(ptr_map.items()):
    off = target_addr - 0x08000000
    text = decode_sjis_at(off)
    if text:
        ui_strings.append((target_addr, text, refs))

print(f"Valid decoded UI strings with pointers: {len(ui_strings)}")
for addr, t, refs in ui_strings[:20]:
    print(f"  0x{addr:08X} ({len(refs)} refs): {t}")
