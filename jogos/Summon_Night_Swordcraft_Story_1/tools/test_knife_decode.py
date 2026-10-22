import struct
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")
rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
off = 0x081E87D8 - 0x08000000

name = rom[off : off + 0x28].split(b"\x00")[0].decode("shift-jis")
desc = rom[off + 0x42 : off + 0x90].split(b"\x00")[0].decode("shift-jis")
print("Name:", name)
print("Desc:", desc)

# Stats between 0x28 and 0x42:
stats = rom[off + 0x28 : off + 0x42]
print("Stats hex:", stats.hex(" "))
