import json
import sys

sys.stdout.reconfigure(encoding="utf-8")
with open("extracted/all_static_strings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for s in data:
    txt = s["text"]
    if any(k in txt.lower() for k in ["herb", "leaf", "potion", "bandana", "ring", "boots", "ore", "mineral", "iron"]):
        print(f"{s['addr']}: {txt}")
