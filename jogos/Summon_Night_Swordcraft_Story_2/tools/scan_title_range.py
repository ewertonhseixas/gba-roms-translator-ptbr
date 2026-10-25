import struct
from pathlib import Path

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
rom = rom_path.read_bytes()

# Search between 0x080000 and 0x0A0000 for any strings
def scan_printable(data, start, end):
    results = []
    p = start
    while p + 1 < end:
        w = struct.unpack_from('>H', data, p)[0]
        if 0x8260 <= w <= 0x8279 or 0x8281 <= w <= 0x829A:
            # candidate SJIS string
            chars = []
            s_off = p
            while p + 1 < end:
                w2 = struct.unpack_from('>H', data, p)[0]
                p += 2
                if w2 == 0:
                    break
                elif 0x8260 <= w2 <= 0x8279: chars.append(chr(ord('A') + w2 - 0x8260))
                elif 0x8281 <= w2 <= 0x829A: chars.append(chr(ord('a') + w2 - 0x8281))
                elif 0x824F <= w2 <= 0x8258: chars.append(chr(ord('0') + w2 - 0x824F))
                elif w2 == 0x8140: chars.append(' ')
                elif w2 == 0x8143: chars.append(',')
                elif w2 == 0x8144: chars.append('.')
                elif w2 == 0x8148: chars.append('?')
                elif w2 == 0x8149: chars.append('!')
                elif w2 == 0x8166: chars.append("'")
                elif w2 == 0x8168: chars.append('"')
                elif w2 == 0x8163: chars.append('…')
                elif w2 == 0x817C: chars.append('-')
                else: break
            s = ''.join(chars).strip()
            if len(s) >= 2:
                results.append((s_off, s))
        else:
            p += 2
    return results

print("Strings in 0x080000..0x095000:")
for off, s in scan_printable(rom, 0x080000, 0x095000):
    print(f"  0x{off:06X} (0x{0x08000000+off:08X}): {s}")
