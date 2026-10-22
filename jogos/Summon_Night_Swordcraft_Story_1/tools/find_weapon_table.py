import struct
from pathlib import Path

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()

# Look at references to 0x081E88F8 or pointers around 0x081E0000 - 0x081F0000
addr = 0x081E88F8
target_bytes = struct.pack("<I", addr)

print(f"Searching for pointer to Chaves's Sword (0x{addr:08X})...")
for off in range(0, 0x200000, 4):
    if rom[off:off+4] == target_bytes:
        print(f"  Pointer found at 0x{off + 0x08000000:08X} (offset 0x{off:06X})")
