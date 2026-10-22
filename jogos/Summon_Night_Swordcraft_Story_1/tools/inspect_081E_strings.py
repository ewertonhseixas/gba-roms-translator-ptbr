import json

with open("extracted/all_static_strings.json", "r", encoding="utf-8") as f:
    data = json.load(f)

count = 0
for s in data:
    addr = int(s["addr"], 16)
    if 0x081E0000 <= addr <= 0x081F8000:
        print(f"{s['addr']}: {s['text']}")
        count += 1
        if count > 40: break

print(f"Total strings in 0x081E0000..0x081F8000: {count}")
