import struct
from pathlib import Path

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
rom = rom_path.read_bytes()

def decode_sjis_run(data, offset, length=500):
    res = []
    p = offset
    end = min(len(data), offset + length)
    while p + 1 < end:
        w = struct.unpack_from('>H', data, p)[0]
        p += 2
        if w == 0:
            if res:
                yield (offset, ''.join(res))
                res = []
            offset = p
        elif 0x8260 <= w <= 0x8279: res.append(chr(ord('A') + w - 0x8260))
        elif 0x8281 <= w <= 0x829A: res.append(chr(ord('a') + w - 0x8281))
        elif 0x824F <= w <= 0x8258: res.append(chr(ord('0') + w - 0x824F))
        elif w == 0x8140: res.append(' ')
        elif w == 0x8144: res.append('.')
        elif w == 0x8143: res.append(',')
        elif w == 0x8149: res.append('!')
        elif w == 0x8148: res.append('?')
        elif w == 0x8166: res.append("'")
        elif w == 0x8168: res.append('"')
        elif w == 0x8163: res.append('…')
        elif w == 0x817C: res.append('-')
        else:
            if len(res) > 3:
                yield (offset, ''.join(res))
            res = []
            offset = p

print("--- Strings around 0x08F000 ---")
for off, s in list(decode_sjis_run(rom, 0x08F000, 3000))[:20]:
    print(f"0x{off:06X} (0x{0x08000000+off:08X}): {s}")

print("\n--- Strings around 0x4F0000 ---")
for off, s in list(decode_sjis_run(rom, 0x4F0000, 5000))[:20]:
    print(f"0x{off:06X} (0x{0x08000000+off:08X}): {s}")
