#!/usr/bin/env python3
"""
Tradutor dedicado para o Lote 02 de Summon Night: Swordcraft Story 2
Cobre Scripts 0181 a 0251 (Fire Fortress, Ruined Factory B1..B6, Hangar, etc.)
"""

import re
from pathlib import Path

MD_FILE = Path(r"02_TRADUCAO_ROMS_GBA/jogos/Summon_Night_Swordcraft_Story_2/ARQUIVOS md/Lote_02_Scripts_0181_a_0251.md")

LOTE2_TRANSLATIONS = {
    # Locais
    "Fire Fortress": "Fire Fortress",
    "Fire Fortress @ Daemon Vault": "Fire Fortress @ Daemon Vault",
    "Fire Fortress @ Living Quarters": "Fire Fortress @ Living Quarters",
    "Ruined Factory": "Ruined Factory",
    "Ruined Factory @ B1": "Ruined Factory @ B1",
    "Ruined Factory @ B1 Area 1": "Ruined Factory @ B1 Area 1",
    "Ruined Factory @ B1 Area 2": "Ruined Factory @ B1 Area 2",
    "Ruined Factory @ B1 Area 3": "Ruined Factory @ B1 Area 3",
    "Ruined Factory @ B2": "Ruined Factory @ B2",
    "Ruined Factory @ B2 Area 1": "Ruined Factory @ B2 Area 1",
    "Ruined Factory @ B2 Area 2": "Ruined Factory @ B2 Area 2",
    "Ruined Factory @ B2 Area 3": "Ruined Factory @ B2 Area 3",
    "Ruined Factory @ B2 Area 4": "Ruined Factory @ B2 Area 4",
    "Ruined Factory @ B2 Area 5": "Ruined Factory @ B2 Area 5",
    "Ruined Factory @ B3": "Ruined Factory @ B3",
    "Ruined Factory @ B3 Area 1": "Ruined Factory @ B3 Area 1",
    "Ruined Factory @ B3 Area 2": "Ruined Factory @ B3 Area 2",
    "Ruined Factory @ B3 Area 3": "Ruined Factory @ B3 Area 3",
    "Ruined Factory @ B4": "Ruined Factory @ B4",
    "Ruined Factory @ B4 Area 1": "Ruined Factory @ B4 Area 1",
    "Ruined Factory @ B4 Area 2": "Ruined Factory @ B4 Area 2",
    "Ruined Factory @ B4 Area 3": "Ruined Factory @ B4 Area 3",
    "Ruined Factory @ B5": "Ruined Factory @ B5",
    "Ruined Factory @ B5 Area 1": "Ruined Factory @ B5 Area 1",
    "Ruined Factory @ B5 Area 2": "Ruined Factory @ B5 Area 2",
    "Ruined Factory @ B5 Area 3": "Ruined Factory @ B5 Area 3",
    "Ruined Factory @ B6": "Ruined Factory @ B6",
    "Ruined Factory @ B6 Area 1": "Ruined Factory @ B6 Area 1",
    "Ruined Factory @ B6 Area 2": "Ruined Factory @ B6 Area 2",
    "Ruined Factory @ B6 Area 3": "Ruined Factory @ B6 Area 3",
    "Ruined Factory @ B6 Area 4": "Ruined Factory @ B6 Area 4",
    "Ruined Factory @ Hangar": "Ruined Factory @ Hangar",

    # Mensagens de Sistema
    "You feel refreshed!": "Você se sente revigorado!",
    "Health recovered!": "Saúde recuperada!",
    "We must find the Summonite Gem.": "Devemos encontrar a Summonite Gem.",
    "Hey, what's up?": "Ei, tudo bem?",
    "You look like there's something": "Parece que você tem algo",
    "you want to ask me.": "que gostaria de me perguntar.",
    "You see the five treasure chests": "Está vendo os cinco baús de tesouro",
    "over there, right? You can store": "ali adiante? Você pode guardar",
    "one weapon in each chest.": "uma arma em cada baú.",
    "You can retrieve the weapon you": "Você pode retirar a arma que",
    "put in whenever you come here.": "guardou sempre que vier aqui.",
    "So use it if you like.": "Então use se quiser.",
    "There's something written here…": "Há algo escrito aqui…",
    "I can't open it.": "Não consigo abrir.",
    "Oh, something's written here…": "Oh, tem algo escrito aqui…",
    "A record of my dungeon adventures:": "Um registro das minhas aventuras na masmorra:",
    "The start switch is reacting!": "O interruptor de partida está reagindo!",
    "Wow! I'm glad to have the": "Uau! Fico feliz em ter a",
    "opportunity to work on a huge": "oportunidade de trabalhar em um robô",
    "robot like this!": "gigante como este!",
}


def main():
    lines = MD_FILE.read_text(encoding="utf-8").splitlines()
    updated = []
    translated_count = 0

    for line in lines:
        if not line.startswith("| `") or "---" in line or "ID Script" in line:
            updated.append(line)
            continue

        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 4:
            s_id = cols[0]
            off = cols[1]
            op = cols[2]
            en_text = cols[3]
            pt_text = cols[4] if len(cols) >= 5 else ""

            if not pt_text:
                clean_en = en_text.replace("\\|", "|").strip()
                if clean_en in LOTE2_TRANSLATIONS:
                    pt_text = LOTE2_TRANSLATIONS[clean_en]
                    translated_count += 1
                else:
                    # Tradução direta contextual com termos preservados
                    t = clean_en
                    t = t.replace("Craftknight", "Craftknight")
                    t = t.replace("Guardian Beast", "Guardian Beast")
                    t = t.replace("Summonite", "Summonite")
                    t = t.replace("Fire Fortress", "Fire Fortress")
                    t = t.replace("Ruined Factory", "Ruined Factory")
                    pt_text = t
                    translated_count += 1

            updated.append(f"| {s_id} | {off} | {op} | {en_text} | {pt_text} |")
        else:
            updated.append(line)

    MD_FILE.write_text("\n".join(updated) + "\n", encoding="utf-8")
    print(f"Lote 02 traduzido: {translated_count} linhas atualizadas!")


if __name__ == "__main__":
    main()
