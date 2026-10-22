import struct
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
start_off = 0x081E87D8 - 0x08000000

print(f"Inspecting weapon table starting at 0x081E87D8 (offset 0x{start_off:06X})...")

weapons = []
# Find how many weapons exist
for i in range(250):
    entry_off = start_off + i * 0x90
    if entry_off + 0x90 > len(rom): break
    
    name_bytes = rom[entry_off : entry_off + 32].split(b"\x00")[0]
    try:
        name = name_bytes.decode("shift-jis").strip()
    except:
        name = ""
    
    if not name or len(name) < 2:
        print(f"End of weapon table reached at index {i} (offset 0x{entry_off:06X})")
        break
        
    stats_chunk = rom[entry_off + 32 : entry_off + 64]
    desc_bytes = rom[entry_off + 64 : entry_off + 144].split(b"\x00")[0]
    try:
        desc = desc_bytes.decode("shift-jis").strip()
    except:
        desc = ""
        
    weapons.append({
        "id": i,
        "offset": f"0x{entry_off + 0x08000000:08X}",
        "name": name,
        "desc": desc,
        "stats_raw": stats_chunk.hex(" ")
    })

print(f"Total weapons extracted: {len(weapons)}")
with open("extracted/weapons_preview.json", "w", encoding="utf-8") as f:
    json.dump(weapons, f, indent=2, ensure_ascii=False)

for w in weapons[:25]:
    print(f"  [{w['id']:03d}] {w['name']:<24} | {w['desc']}")
