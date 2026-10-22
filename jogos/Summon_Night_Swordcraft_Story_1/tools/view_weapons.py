import json
import sys
sys.stdout.reconfigure(encoding="utf-8")

with open("extracted/weapons_preview.json", "r", encoding="utf-8") as f:
    weps = json.load(f)

for w in weps[:30]:
    print(f"[{w['id']:03d}] {w['name']:<24} | {w['desc']}")
