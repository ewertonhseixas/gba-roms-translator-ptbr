import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
off = 0x1EEFE8

print(f"Inspecting table after weapons (offset 0x{off:06X})...")
for i in range(0, 512, 16):
    chunk = rom[off+i : off+i+16]
    ascii_chunk = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
    try:
        sjis = chunk.split(b"\x00")[0].decode("shift-jis").strip()
    except:
        sjis = ""
    print(f"  [0x{off+i:06X}]: {chunk.hex(' ')} | {sjis}")
