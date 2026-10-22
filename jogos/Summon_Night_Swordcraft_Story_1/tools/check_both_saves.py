import struct
from pathlib import Path

for name in ["Summon Night - Swordcraft Story (USA).sav", "Summon Night - Swordcraft Story (PT-BR).sav"]:
    sav = Path(f"rom/{name}").read_bytes()
    non_zero = sum(1 for b in sav if b != 0x00 and b != 0xFF)
    print(f"{name}: {len(sav)} bytes, non-zero/FF bytes: {non_zero}")
    if non_zero > 0:
        for i in range(0, min(len(sav), 512), 16):
            c = sav[i:i+16]
            print(f"  [0x{i:03X}]: {c.hex(' ')}")
