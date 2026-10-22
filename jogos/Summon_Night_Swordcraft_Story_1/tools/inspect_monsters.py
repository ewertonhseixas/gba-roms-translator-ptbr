import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
with open("extracted/all_static_strings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

monsters = []
for s in data:
    addr = int(s["addr"], 16)
    if 0x081F7000 <= addr <= 0x081FC000:
        monsters.append(s)

print(f"Total entries in 0x081F7000..0x081FC000: {len(monsters)}")
for m in monsters[:30]:
    print(f"  {m['addr']}: {m['text']}")
