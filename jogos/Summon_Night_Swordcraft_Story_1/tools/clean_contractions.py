import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.dirname(BASE_DIR)
JSON_PATH = os.path.join(GAME_DIR, 'extracted', 'translation_pack_ptbr.json')

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    pack = json.load(f)

scripts = pack['scripts']

# 1. Inspect and fix cê
print("=== CÊ HITS ===")
for s_id, s_data in scripts.items():
    for e in s_data.get('strings', []):
        pt = e.get('ptbr', '')
        if re.search(r'\bcê\b', pt, re.IGNORECASE):
            print(f"#{s_id} [{e['id']}]: {pt}")
            # Replace cê -> você
            new_pt = re.sub(r'\bcê\b', 'você', pt, flags=re.IGNORECASE)
            if len(new_pt) <= 35:
                e['ptbr'] = new_pt

# 2. Inspect and fix né?
print("\n=== NÉ? HITS ===")
for s_id, s_data in scripts.items():
    for e in s_data.get('strings', []):
        pt = e.get('ptbr', '')
        if 'né?' in pt:
            print(f"#{s_id} [{e['id']}]: {pt}")
            cand1 = pt.replace('né?', 'não é?')
            cand2 = pt.replace('né?', 'certo?')
            if len(cand1) <= 35:
                e['ptbr'] = cand1
            elif len(cand2) <= 35:
                e['ptbr'] = cand2

# 3. Clean tá -> está safely
print("\n=== CLEANING TÁ ===")
t_fixed = 0
for s_id, s_data in scripts.items():
    for e in s_data.get('strings', []):
        pt = e.get('ptbr', '')
        if re.search(r'\btá\b', pt):
            # Check if replacing tá with está fits
            cand = re.sub(r'\btá\b', 'está', pt)
            cand = re.sub(r'\bTá\b', 'Está', cand)
            if all(len(line) <= 35 for line in cand.split('\n')):
                e['ptbr'] = cand
                t_fixed += 1
print(f"Fixed {t_fixed} occurrences of tá -> está")

# 4. Clean pra -> para safely
print("\n=== CLEANING PRA ===")
p_fixed = 0
for s_id, s_data in scripts.items():
    for e in s_data.get('strings', []):
        pt = e.get('ptbr', '')
        if re.search(r'\bpra\b', pt, re.IGNORECASE):
            cand = re.sub(r'\bpra\b', 'para', pt)
            cand = re.sub(r'\bPra\b', 'Para', cand)
            if all(len(line) <= 35 for line in cand.split('\n')):
                e['ptbr'] = cand
                p_fixed += 1
print(f"Fixed {p_fixed} occurrences of pra -> para")

# 5. Clean pro -> para o safely
print("\n=== CLEANING PRO ===")
pro_fixed = 0
for s_id, s_data in scripts.items():
    for e in s_data.get('strings', []):
        pt = e.get('ptbr', '')
        if re.search(r'\bpro\b', pt, re.IGNORECASE):
            cand = re.sub(r'\bpro\b', 'para o', pt)
            cand = re.sub(r'\bPro\b', 'Para o', cand)
            if all(len(line) <= 35 for line in cand.split('\n')):
                e['ptbr'] = cand
                pro_fixed += 1
print(f"Fixed {pro_fixed} occurrences of pro -> para o")

# Save
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(pack, f, indent=2, ensure_ascii=False)

print(f"\nSaved cleaned {JSON_PATH}")
