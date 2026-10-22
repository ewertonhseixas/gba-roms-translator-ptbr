import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("extracted/game_data/weapons.json", "r", encoding="utf-8") as f:
    weps = json.load(f)

for w in weps[:8]:
    print(f"[{w['id']:03d}] {w['name']:<20} | ATK: {w['atk']:3d} | DUR: {w['durability']:3d}/{w['max_durability']:3d} | {w['description']}")
