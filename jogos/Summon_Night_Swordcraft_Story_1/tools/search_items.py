import json

with open("extracted/all_static_strings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for s in data:
    txt = s["text"]
    if any(k in txt.lower() for k in ["sword", "blade", "axe", "spear", "knuckle", "drill", "potion", "ore", "hammer", "slime"]):
        print(f"{s['addr']}: {txt}")
