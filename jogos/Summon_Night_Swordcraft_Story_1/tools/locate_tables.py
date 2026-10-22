import struct
from pathlib import Path

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()

test_names = [b"Amateur Sword", b"Iron Sword", b"Iron Ore", b"Potion", b"Slime", b"Pawn", b"Centurion", b"Aqua Blade", b"Flame Sword"]
for name in test_names:
    pos = 0
    found = 0
    while True:
        idx = rom.find(name, pos)
        if idx == -1: break
        print(f"Found {name.decode()} at ROM offset 0x{idx:06X} (Addr 0x{idx + 0x08000000:08X})")
        pos = idx + len(name)
        found += 1
        if found > 5: break
