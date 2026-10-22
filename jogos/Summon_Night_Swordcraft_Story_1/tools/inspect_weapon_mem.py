import struct
from pathlib import Path

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
off = 0x081E88F8 - 0x08000000

print(f"Hex dump around 0x081E88F8 (offset 0x{off:06X}):")
for i in range(-64, 128, 16):
    chunk = rom[off+i : off+i+16]
    ascii_chunk = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    print(f"  [0x{off+i:06X}]: {chunk.hex(' ')} | {ascii_chunk}")
