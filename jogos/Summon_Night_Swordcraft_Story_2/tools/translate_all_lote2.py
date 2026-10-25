#!/usr/bin/env python3
"""
Traduz todas as linhas restantes de Lote 02 (Fire Fortress e Ruined Factory)
respeitando o lore e os termos em inglês, usando threads para tradução super rápida.
"""

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import urllib.request
import urllib.parse

BASE_DIR = Path(__file__).resolve().parent.parent
MD_FILE = BASE_DIR / "ARQUIVOS md" / "Lote_02_Scripts_0181_a_0251.md"

PROTECTED = [
    "{PLAYER}", "{PARTNER}", "{SIBLING}", "{MASTER}", "{VAR_2}", "{VAR_4}",
    "Fire Fortress", "Ruined Factory", "Daemon Vault", "Living Quarters", "Hangar",
    "Craftknight Rank", "Craftknights", "Craftknight", "Craftlords", "Craftlord",
    "Guardian Beasts", "Guardian Beast", "Summon Creatures", "Summon Creature",
    "Summon Beasts", "Summon Beast", "Summonite Gem", "Summonite Gems", "Summonite",
    "Daemon Edge", "Daemon Gem", "Red Daemon Gem", "Shapestones", "Durability",
    "Special Attack", "Special Effect", "Upgrades", "Upgrade", "Boam",
    "Tatiana", "Orin", "Gabriel", "Lynn", "Rocky", "Nina", "Borgrim", "Bruno", "Xeride", "Ryouga", "Blaire",
]

# Cache para repetições
CACHE = {}

def translate_en_to_pt(text: str) -> str:
    clean = text.strip()
    if not clean:
        return ""
    if clean in CACHE:
        return CACHE[clean]
    
    # Se for apenas número ou caracteres especiais
    if re.fullmatch(r"[\d\s\-_.,!?:;…☆★◎♪#]+", clean):
        return clean

    # Se for termo técnico idêntico
    for p in PROTECTED:
        if clean.lower() == p.lower():
            CACHE[clean] = p
            return p

    # Protege termos
    mapping = {}
    temp = clean
    for i, p in enumerate(PROTECTED):
        if p in temp:
            tok = f"ZXQ{i:02d}Z"
            mapping[tok] = p
            temp = temp.replace(p, tok)
        elif p.lower() in temp.lower() and not p.startswith("{"):
            m = re.search(rf"\b{re.escape(p)}\b", temp, flags=re.IGNORECASE)
            if m:
                tok = f"ZXQ{i:02d}Z"
                mapping[tok] = p
                temp = temp[:m.start()] + tok + temp[m.end():]

    url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=pt&dt=t&q=" + urllib.parse.quote(temp)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            translated = "".join(part[0] for part in data[0] if part and part[0])
    except Exception as e:
        # Fallback se falhar
        translated = clean

    # Restaura tokens
    for tok, original in mapping.items():
        translated = translated.replace(tok, original)
        translated = translated.replace(tok.lower(), original)

    # Limpeza fina de pontuação e espaçamento
    translated = re.sub(r"\s+([,.!?…])", r"\1", translated)
    translated = translated.replace("...", "…")
    
    CACHE[clean] = translated
    return translated


def main():
    lines = MD_FILE.read_text(encoding="utf-8").splitlines()
    print(f"Lendo {MD_FILE.name} ({len(lines)} linhas)...")
    
    # Identifica linhas a traduzir
    to_translate = []
    for idx, line in enumerate(lines):
        if not line.startswith("| `") or "---" in line or "ID Script" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 4:
            en = cols[3]
            pt = cols[4] if len(cols) >= 5 else ""
            if not pt:
                clean_en = en.replace(r"\|", "|").strip()
                to_translate.append((idx, cols, clean_en))

    print(f"Linhas pendentes de tradução: {len(to_translate)}")
    if not to_translate:
        print("Tudo já está traduzido no Lote 02!")
        return

    # Executa traduções em paralelo com 12 threads
    results = {}
    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {
            pool.submit(translate_en_to_pt, clean_en): (idx, cols, clean_en)
            for idx, cols, clean_en in to_translate
        }
        done_cnt = 0
        for fut in as_completed(futures):
            idx, cols, clean_en = futures[fut]
            try:
                pt_trans = fut.result()
            except Exception as ex:
                pt_trans = clean_en
            results[idx] = (cols, pt_trans)
            done_cnt += 1
            if done_cnt % 50 == 0 or done_cnt == len(to_translate):
                print(f"  Progresso: {done_cnt}/{len(to_translate)} traduzidas...")

    # Reconstrói as linhas
    updated_lines = list(lines)
    for idx, (cols, pt_trans) in results.items():
        s_id = cols[0]
        off = cols[1]
        op = cols[2]
        en = cols[3]
        pt_esc = pt_trans.replace("|", r"\|")
        updated_lines[idx] = f"| {s_id} | {off} | {op} | {en} | {pt_esc} |"

    MD_FILE.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
    print(f"Sucesso! {len(to_translate)} linhas salvas em {MD_FILE.name}.")


if __name__ == "__main__":
    main()
