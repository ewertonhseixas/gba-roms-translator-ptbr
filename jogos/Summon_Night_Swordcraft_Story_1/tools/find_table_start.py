import struct
from pathlib import Path

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()

# Let's search backwards from 0x1E88F8 for the first weapon
# Weapon names start with Shift-JIS: 0x82...
# Let's find all entries in this block
start_off = 0x1E0000
end_off = 0x1F0000

# Let's search for the first occurrence of weapon type headers or names
for off in range(0x1E0000, 0x1E88F8, 16):
    chunk = rom[off:off+32]
    try:
        s = chunk.split(b"\x00")[0].decode("shift-jis")
        if len(s) >= 4 and any(w in s.lower() for w in ["sword", "blade", "knife", "saber", "katana", "amateur", "iron"]):
            print(f"Found weapon candidate at 0x{off:06X}: {s}")
    except:
        pass
