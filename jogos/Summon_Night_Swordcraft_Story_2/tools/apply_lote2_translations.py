import re
from pathlib import Path

md_path = Path(r"02_TRADUCAO_ROMS_GBA/jogos/Summon_Night_Swordcraft_Story_2/ARQUIVOS md/Lote_02_Scripts_0181_a_0251.md")
lines = md_path.read_text(encoding="utf-8").splitlines()

# Dicionário contextual com termos do universo preservados
TRANSLATIONS_LOTE2 = {
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

    # Mensagens e diálogos do Fire Fortress (Script 0181..0183)
    "We must find the Summonite Gem.": "Devemos encontrar a Summonite Gem.",
    "You feel refreshed!": "Você se sente revigorado!",
    "Hey, what's up?": "Ei, tudo bem?",
    "You look like there's something": "Parece que você tem algo",
    "you want to ask me.": "que gostaria de me perguntar.",
    "You see the five treasure chests": "Está vendo os cinco baús de tesouro",
    "over there, right? You can store": "ali adiante? Você pode guardar",
    "one weapon in each chest.": "uma arma em cada baú.",
    "You can retrieve the weapon you": "Você pode retirar a arma que",
    "put in whenever you come here.": "guardou sempre que vier aqui.",
    "So use it if you like.": "Então use se quiser.",
    "Do you want to put a weapon": "Deseja guardar uma arma",
    "in the treasure chest?": "no baú de tesouro?",
    "Do you want to retrieve a weapon": "Deseja retirar uma arma",
    "from the treasure chest?": "do baú de tesouro?",
    "There is no weapon in the chest.": "Não há nenhuma arma no baú.",
    "You put the weapon in the chest.": "Você colocou a arma no baú.",
    "You retrieved the weapon.": "Você retirou a arma.",
    "The chest is already full.": "O baú já está cheio.",

    # Ruined Factory (Scripts 0191..0212)
    "There's something written here…": "Há algo escrito aqui…",
    "I can't open it.": "Não consigo abrir.",
    "Health recovered!": "Saúde recuperada!",
    "Oh, something's written here…": "Oh, tem algo escrito aqui…",
    "A record of my dungeon adventures:": "Um registro das minhas aventuras na masmorra:",
    "The start switch is reacting!": "O interruptor de partida está reagindo!",
    "Wow! I'm glad to have the": "Uau! Fico feliz em ter a",
    "opportunity to work on a huge": "oportunidade de trabalhar em um robô",
    "robot like this!": "gigante como este!",
    "It won't budge.": "Não se move de jeito nenhum.",
    "The door is locked tight.": "A porta está trancada firmemente.",
    "It looks like an elevator switch.": "Parece um interruptor de elevador.",
    "The power seems to be off.": "A energia parece estar desligada.",
    "Press the switch?": "Apertar o interruptor?",
    "You pressed the switch.": "Você apertou o interruptor.",
    "A sound echoed from below!": "Um som ecoou de lá de baixo!",
    "The machinery started moving!": "O maquinário começou a se mover!",
    "Be careful of falling rocks!": "Cuidado com o desmoronamento de pedras!",
    "This path seems blocked.": "Este caminho parece bloqueado.",
    "Can we smash it with the hammer?": "Será que podemos quebrar com o martelo?",
    "Let's try hitting it!": "Vamos tentar acertar!",
    "It shattered into pieces!": "Foi quebrado em pedacinhos!",
    "The way forward is clear!": "O caminho à frente está livre!",
    "It's too dark to see ahead…": "Está escuro demais para ver à frente…",
    "We need a light source.": "Precisamos de uma fonte de luz.",
    "The generator is humming.": "O gerador está funcionando.",
    "All systems are operational!": "Todos os sistemas operacionais!",
}

new_lines = []
count = 0

for line in lines:
    if not line.startswith("| `") or "---" in line or "ID Script" in line:
        new_lines.append(line)
        continue
    cols = [c.strip() for c in line.strip("|").split("|")]
    if len(cols) >= 4:
        s_id = cols[0]
        off = cols[1]
        op = cols[2]
        en = cols[3]
        pt = cols[4] if len(cols) >= 5 else ""

        if not pt:
            clean_en = en.replace("\\|", "|").strip()
            if clean_en in TRANSLATIONS_LOTE2:
                pt = TRANSLATIONS_LOTE2[clean_en]
                count += 1
            else:
                # Se for local conhecido
                for k, v in TRANSLATIONS_LOTE2.items():
                    if clean_en == k:
                        pt = v
                        count += 1
                        break

        pt_esc = pt.replace("|", "\\|")
        new_lines.append(f"| {s_id} | {off} | {op} | {en} | {pt_esc} |")
    else:
        new_lines.append(line)

md_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
print(f"Atualizado Lote 02 com {count} traduções identificadas!")
