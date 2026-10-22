import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()

# Search before 0x1E87D8 for Shift-JIS strings
for off in range(0x1E0000, 0x1E87D8, 4):
    chunk = rom[off:off+32]
    try:
        s = chunk.split(b"\x00")[0].decode("shift-jis").strip()
        if len(s) >= 4 and any(w in s.lower() for w in ["ore", "potion", "water", "ring", "boots", "herb", "stone", "iron"]):
            print(f"Found item candidate at 0x{off:06X} (0x{off+0x08000000:08X}): {s}")
    except:
        pass
