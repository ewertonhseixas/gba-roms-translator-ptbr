import struct
from pathlib import Path

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
off = 0x081E87D8 - 0x08000000

print(f"Novice Knife raw dump (144 bytes = 0x90):")
for i in range(0, 0x90, 4):
    val = struct.unpack_from("<I", rom, off + i)[0]
    ptr_str = ""
    if 0x08000000 <= val < 0x08800000:
        target = val - 0x08000000
        sample = rom[target:target+32].split(b"\x00")[0]
        try:
            ptr_str = f"-> PTR to '{sample.decode('shift-jis')}'"
        except:
            ptr_str = f"-> PTR (raw: {sample[:10].hex()})"
    print(f"  [+0x{i:02X}]: 0x{val:08X} ({val:8d}) {ptr_str}")
