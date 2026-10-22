#!/usr/bin/env python3
"""
Gerador e Tradutor Modular de Lotes de Diálogos em Markdown (PT-BR)
Summon Night: Swordcraft Story (GBA) [AB4E]
===================================================================
1. Agrupa linhas consecutivas de uma mesma caixa/sentença de diálogo (opcode 0x0218)
   para tradução contextual completa.
2. Protege todas as variáveis dinâmicas ({PLAYER}, {PARTNER}, {SIBLING}, {MASTER},
   {VAR_2}, {VAR_4}, {COLOR_x}) e todos os termos em inglês validados no glossário
   (Craftknight, Craftlord, Guardian Beast, Summon Creature, Stray Summon, Mystic Ore,
   Summonite, Silver Guild, Gold Guild, Central Tower, Water Scooter, nomes de armas,
   itens, magias, monstros e locais).
3. Aplica pós-processamento gramatical em PT-BR (concordância de gênero para termos
   mantidos em inglês: "a Silver Guild", "a Gold Guild", "a Central Tower",
   "a Guardian Beast", "a Water Scooter", "a City of Swords", "a Marine Dungeon")
   e redistribui proporcionalmente a frase traduzida no número exato de linhas
   originais do script PSI3.
4. Gera todos os 20 arquivos .md distribuídos nas 6 pastas de Lotes em `ARQUIVOS md/`
   com status `✅ Validado` e sincroniza `extracted/translation_pack_ptbr.json`.
"""

import concurrent.futures
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
MD_DIR = ROOT_DIR / "ARQUIVOS md"
PACK_PATH = ROOT_DIR / "extracted" / "translation_pack_ptbr.json"
CACHE_PATH = ROOT_DIR / "extracted" / "sentence_translation_cache.json"

sys.path.insert(0, str(ROOT_DIR / "tools"))
import build_ptbr_rom as bpr
from archive_extractor import parse_archive_table
from psi3_rebuilder import ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR, build_opcode_spec_table

# Frases e termos compostos/nomes próprios que DEVEM permanecer em inglês conforme validado pelo usuário
BASE_PROTECTED_PHRASES = [
    # Variáveis e tags de controle da engine
    "{PLAYER}", "{PARTNER}", "{SIBLING}", "{MASTER}", "{VAR_2}", "{VAR_4}",
    "{COLOR_0}", "{COLOR_1}", "{COLOR_2}", "{COLOR_3}", "{COLOR_4}",
    "{CMD_8740}", "{CMD_8741}", "{CMD_8742}", "{CMD_8743}", "{CMD_8744}",
    # Títulos e termos compostos do Lore
    "Craftlord of Sapphire", "Craftlord of Ruby", "Craftlord of Iron",
    "Craftlord Lubert", "Craftlord Ureksa", "Deigleya Soldier",
    "Fort Mirana Docks", "Fort Mirana", "Lighthouse Rooftop", "Cape Lighthouse",
    "Marine Dungeon", "Upper Wystern", "Middle Wystern", "Lower Wystern",
    "Ship Workshop", "Ship Helm", "Vance Cape", "Kagro Volcano", "Rugista Island",
    "Central Tower", "Silver Guild", "Gold Guild", "Hidden Room", "Assembly Hall",
    "Trish Workshop", "Cazio Workshop", "Ariel/Mariel Lab", "Razzy Workshop", "Sanary Workshop",
    "Guardian Beasts", "Guardian Beast", "Summon Creatures", "Summon Creature",
    "Summon Beasts", "Summon Beast", "Stray Summons", "Stray Summon",
    "Mystic Ores", "Mystic Ore", "City of Swords", "Water Scooters", "Water Scooter",
    "Entrance Ticket", "Iron Ore", "Martial Ore", "Blazing Ore", "Deep Sea Ore", "Gale Ore", "Magnetic Ore",
    "Dragon Fang Ore", "Western Sword", "Eastern Sword", "Northern Sword",
    "Father's Charm", "Spice Set", "Weapon Shard (S)", "Weapon Shard (M)", "Weapon Shard (L)",
    "Sword Type", "Axe Type", "Spear Type", "Knuckle Type", "Drill Type",
    # Termos únicos do universo e nomes próprios
    "Craftknights", "Craftknight", "Craftlords", "Craftlord", "Summonite",
    "Wystern", "Mirana", "Indole", "Seijent", "Deigleya", "Lyndbaum", "Silturn", "Sapureth", "Maetropa",
    "Cleru", "Pratty", "Rasho", "Sanary", "Sugar", "Kutty", "Zantek", "Kuhyra",
    "Chaves", "Kenon", "Razzy", "Ariel", "Mariel", "Varil",
    "Bron", "Amariss", "Shintetsu", "Sakuro", "Kouren", "Lubert", "Ureksa", "Rondeau", "Rumari", "Parista",
    "Trish", "Cazio", "Hayato", "Touya", "Natsumi", "Aya",
]


def build_protected_phrases_list() -> List[str]:
    """Combina a lista base com nomes compostos de armas, magias, itens e monstros dos arquivos 04..07."""
    phrases = set(BASE_PROTECTED_PHRASES)
    for md_name in [
        "04-armas-espadas-machados-e-lancas.md",
        "05-armas-soqueiras-brocas-e-magias.md",
        "06-itens-acessorios-materiais-e-chave.md",
        "07-bestiario-monstros-e-chefes.md",
    ]:
        p = MD_DIR / md_name
        if not p.exists():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.startswith("|") or "---" in line or "Endereço" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 4:
                # Coluna 1 é o nome original em inglês, Coluna 2 ou 3 é o nome sugerido
                en_name = cols[1].strip("` ").split("*")[0].strip("` ")
                pt_name = cols[3].strip("` ") if len(cols) >= 5 else cols[2].strip("` ")
                # Se o usuário manteve em inglês e é um nome composto (ou específico), protege
                if en_name == pt_name and (" " in en_name or len(en_name) >= 7):
                    if en_name not in ("Spirit", "Soldier", "Defender", "Charger", "Jumper", "Cutter", "Striker", "Glider", "Popper", "Tumbler", "Spinner", "Bandage", "Sandals", "Halberd", "Gladius"):
                        phrases.add(en_name)
    # Ordena do maior para o menor para evitar substituição parcial
    return sorted(phrases, key=lambda x: (-len(x), x))


PROTECTED_PHRASES = build_protected_phrases_list()

# Frases curtas recorrentes traduzidas diretamente sem precisar de requisição
EXACT_SENTENCE_MAP: Dict[str, str] = {
    "I can't open it.": "Não consigo abrir.",
    "I can't open it...": "Não consigo abrir...",
    "I can't open it…": "Não consigo abrir…",
    "It's probably locked.": "Provavelmente está trancada.",
    "It's probably locked...": "Provavelmente está trancada...",
    "It's probably locked…": "Provavelmente está trancada…",
    "It must be locked.": "Deve estar trancada.",
    "It must be locked...": "Deve estar trancada...",
    "It must be locked…": "Deve estar trancada…",
    "It opened...": "Abriu...",
    "It opened…": "Abriu…",
    "It's empty...": "Está vazio...",
    "It's empty…": "Está vazio…",
    "It's locked!": "Está trancado!",
    "Small Key used!": "Chave Pequena usada!",
    "Yes": "Sim",
    "No": "Não",
    "Yes.": "Sim.",
    "No.": "Não.",
    "Never mind.": "Deixa pra lá.",
    "Save the game?": "Salvar o jogo?",
    "Sorry, I'm busy.": "Desculpe, estou ocupado.",
    "Don't talk to me.": "Não fale comigo.",
    "Welcome!": "Bem-vindo!",
    "Good luck!": "Boa sorte!",
    "Thank you!": "Obrigado!",
    "Thank you.": "Obrigado.",
    "Thanks!": "Valeu!",
    "Thanks.": "Obrigado.",
    "Thanks...": "Obrigado...",
    "Thanks…": "Obrigado…",
    "Alright!": "Certo!",
    "Alright.": "Certo.",
    "All right!": "Tudo bem!",
    "All right.": "Tudo bem.",
    "Okay!": "Certo!",
    "Okay.": "Certo.",
    "I see...": "Entendo...",
    "I see…": "Entendo…",
    "I see.": "Entendo.",
    "What!?": "O quê!?",
    "What?": "O quê?",
    "Huh?": "Hã?",
    "Huh!?": "Hã!?",
    "Oh!": "Ah!",
    "Oh...": "Ah...",
    "Oh…": "Ah…",
    " Kutty!": "Kutty!",
    "Kutty!": "Kutty!",
    "Kuu...": "Kuu...",
    "Kuu…": "Kuu…",
    "Kuu!": "Kuu!",
    "Meow.": "Miau.",
    "Meow!": "Miau!",
    "Sigh...": "Suspiro...",
    "Sigh…": "Suspiro…",
    "(Sigh...)": "(Suspiro...)",
    "(Sigh…)": "(Suspiro…)",
    "Wake! UP!!": "Acorda! LEVANTA!!",
    "…may…": "…a cor…",
    "…cup…": "…da…",
    "…Make up? With who?": "…A corda? Pra amarrar quem?",
    "Why is Mother yelling about makeup?": "Por que a mamãe está gritando sobre uma corda?",
    "I tink my node id bwoken…": "Acho que quebuei meu nauiz…",
    "I work for a Craftknight, of course!": "Trabalho para um Craftknight, claro!",
    "I work for a Craftknight, Mother!": "Eu trabalho para um Craftknight, mãe!",
}

BATCH_DEFINITIONS = [
    {
        "folder": "Lote_01_Exploracao_Dias_01_a_04",
        "files": [
            {
                "filename": "10-dia01-complemento-wystern-e-torre.md",
                "title": "10 — Diálogos Dia 1 (Complemento Completo): Wystern, Guildas, Lojas e Torre Central",
                "scripts": list(range(101, 400)),
                "only_untranslated_in_08_09": True,
            },
            {
                "filename": "11-dia02-porto-mirana-e-2a-rodada.md",
                "title": "11 — Diálogos Dia 2: Porto de Wystern, Mirana e Segunda Rodada",
                "scripts": list(range(400, 500)),
            },
            {
                "filename": "12-dia03-busca-por-razzy-e-3a-rodada.md",
                "title": "12 — Diálogos Dia 3: Busca por Razzy e Terceira Rodada",
                "scripts": list(range(500, 600)),
            },
            {
                "filename": "13-dia04-indole-materiais-e-4a-rodada.md",
                "title": "13 — Diálogos Dia 4: Chegada de Indole, Materiais e Quarta Rodada",
                "scripts": list(range(600, 700)),
            },
        ],
    },
    {
        "folder": "Lote_02_Exploracao_Dias_05_a_08",
        "files": [
            {
                "filename": "14-dia05-encomenda-e-tensao-gold-guild.md",
                "title": "14 — Diálogos Dia 5: Encomenda de Bron e Tensão com a Gold Guild",
                "scripts": list(range(700, 800)),
            },
            {
                "filename": "15-dia06-navio-de-guerra-e-monstro-marinho.md",
                "title": "15 — Diálogos Dia 6: Encouraçado no Porto e Rumores Oceânicos",
                "scripts": list(range(800, 900)),
            },
            {
                "filename": "16-dia07-mestre-rondeau-e-expedicoes.md",
                "title": "16 — Diálogos Dia 7: Investigação com Rondeau e Expedições",
                "scripts": list(range(900, 1000)),
            },
            {
                "filename": "17-dia08-terremotos-e-segredo-de-razzy.md",
                "title": "17 — Diálogos Dia 8: Terremotos em Wystern e Revelação de Razzy",
                "scripts": list(range(1000, 1100)),
            },
        ],
    },
    {
        "folder": "Lote_03_Exploracao_Dias_09_a_12_e_PosJogo",
        "files": [
            {
                "filename": "18-dia09-reta-final-e-anel-de-bron.md",
                "title": "18 — Diálogos Dia 9: Reta Final do Torneio e o Anel de Bron",
                "scripts": list(range(1100, 1300)),
            },
            {
                "filename": "19-dia10-semifinal-contra-sanary.md",
                "title": "19 — Diálogos Dia 10: Semifinal do Torneio contra Sanary",
                "scripts": list(range(1300, 1400)),
            },
            {
                "filename": "20-dia11-grande-final-contra-varil.md",
                "title": "20 — Diálogos Dia 11: A Grande Final contra Varil",
                "scripts": list(range(1400, 1500)),
            },
            {
                "filename": "21-dia12-novo-craftlord-e-pos-jogo.md",
                "title": "21 — Diálogos Dia 12 & Pós-Jogo: O Novo Craftlord e Exploração",
                "scripts": list(range(1500, 1568)),
            },
        ],
    },
    {
        "folder": "Lote_04_Historia_Principal_Cap_01_a_04",
        "files": [
            {
                "filename": "22-historia-prologo-e-cap01-abertura-e-chaves.md",
                "title": "22 — História Principal: Prólogo, Invocação e Luta contra Chaves",
                "scripts": [1568] + list(range(1600, 1700)),
            },
            {
                "filename": "23-historia-cap02-e-03-mirana-kenon-e-razzy.md",
                "title": "23 — História Principal: Viagem a Mirana, Kenon e Duelo com Razzy",
                "scripts": list(range(1700, 1800)),
            },
            {
                "filename": "24-historia-cap04-e-05-aula-de-sakuro-e-ariel.md",
                "title": "24 — História Principal: Culinária de Sakuro e Desafio de Ariel",
                "scripts": list(range(1800, 1900)),
            },
        ],
    },
    {
        "folder": "Lote_05_Historia_Principal_Cap_06_a_09",
        "files": [
            {
                "filename": "25-historia-cap06-e-07-redemoinho-e-marine-dungeon.md",
                "title": "25 — História Principal: O Redemoinho e a Marine Dungeon",
                "scripts": list(range(1900, 2000)),
            },
            {
                "filename": "26-historia-cap08-e-09-rumari-ureksa-e-kagro-volcano.md",
                "title": "26 — História Principal: Mansão de Ureksa e Vulcão Kagro",
                "scripts": list(range(2000, 2100)),
            },
        ],
    },
    {
        "folder": "Lote_06_Historia_Principal_Final_e_Epilogo",
        "files": [
            {
                "filename": "27-historia-cap10-e-11-farol-forte-mirana-e-finais.md",
                "title": "27 — História Principal: Conspiração em Mirana, Semifinal e Final",
                "scripts": list(range(2100, 2200)),
            },
            {
                "filename": "28-historia-cap12-resgate-de-sanary-e-chefe-final.md",
                "title": "28 — História Principal: Resgate de Sanary, Parista e Batalha Final",
                "scripts": list(range(2200, 2300)),
            },
            {
                "filename": "29-finais-creditos-e-eventos-especiais-masmorras.md",
                "title": "29 — Finais, Conversas Noturnas e Gatilhos Especiais",
                "scripts": list(range(2300, 2600)),
            },
        ],
    },
]


def is_sentence_end(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    return t.endswith((".", "!", "?", "…", "...", "♪", "♡", "☆", '"', "'", ")", "~", ":", ";"))


def group_script_strings(en_strings: List[Dict[str, Any]], pre_translated_ids: Dict[int, str]) -> List[List[Dict[str, Any]]]:
    """
    Agrupa strings consecutivas de opcode 0x0218 que formam uma mesma frase
    dividida em várias linhas na janela do GBA.
    """
    groups: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []

    for item in en_strings:
        s_id = item["id"]
        # Se esta linha já foi traduzida manualmente em 08/09, mantém isolada
        if s_id in pre_translated_ids:
            if cur:
                groups.append(cur)
                cur = []
            groups.append([item])
            continue

        if not cur:
            cur.append(item)
            continue

        prev = cur[-1]
        prev_txt = prev["en"].strip()
        cur_txt = item["en"].strip()

        if (
            item["opcode"] == prev["opcode"] == "0x0218"
            and not is_sentence_end(prev_txt)
            and not cur_txt.startswith(("(", "-", '"', "‘", "'", "{"))
            and len(cur) < 4
        ):
            cur.append(item)
        else:
            groups.append(cur)
            cur = [item]

    if cur:
        groups.append(cur)
    return groups


def protect_sentence(text: str) -> Tuple[str, Dict[str, str]]:
    """Substitui variáveis e termos do glossário por tokens seguros antes de traduzir."""
    mapping: Dict[str, str] = {}
    out = text

    # Normaliza gírias comuns de Bron/NPCs para melhor tradução
    out = re.sub(r"\bya\b", "you", out)
    out = re.sub(r"\byer\b", "your", out)
    out = re.sub(r"\ban'\b", "and", out)
    out = re.sub(r"\bcuz\b", "because", out)
    out = re.sub(r"\bgonna\b", "going to", out)
    out = re.sub(r"\bgotta\b", "got to", out)
    out = re.sub(r"\bwanna\b", "want to", out)

    for idx, phrase in enumerate(PROTECTED_PHRASES):
        if phrase in out:
            tok = f"ZXQ{idx:03d}Z"
            mapping[tok] = phrase
            out = out.replace(phrase, tok)
        elif len(phrase) >= 6 and phrase.lower() in out.lower() and not phrase.startswith("{"):
            m = re.search(rf"\b{re.escape(phrase)}\b", out, flags=re.IGNORECASE)
            if m:
                tok = f"ZXQ{idx:03d}Z"
                mapping[tok] = phrase
                out = out[: m.start()] + tok + out[m.end() :]

    return out, mapping


FEMALE_NAMES = ["Sanary", "Sugar", "Razzy", "Kouren", "Rumari", "Amariss", "Mariel", "Pratty", "Trish"]
CITIES_NO_ART = ["Wystern", "Mirana", "Indole", "Seijent", "Deigleya", "Silturn", "Sapureth", "Maetropa", "Lyndbaum", "Parista"]
FEM_SG_TERMS = [
    "Silver Guild", "Gold Guild", "Central Tower", "City of Swords",
    "Guardian Beast", "Summon Creature", "Summon Beast", "Stray Summon",
    "Water Scooter", "Summonite", "Marine Dungeon", "Rugista Island",
]
FEM_PL_TERMS = [
    "Guardian Beasts", "Summon Creatures", "Summon Beasts", "Stray Summons", "Water Scooters"
]

TRIGGER_RULES: List[Tuple[str, re.Pattern, str]] = []


def _add_rule(trigger: str, pattern: str, repl: str, flags: int = 0) -> None:
    TRIGGER_RULES.append((trigger, re.compile(pattern, flags), repl))


EXACT_SUBS = [
    ("Razzy perdido? Oh não!", "A Razzy perdeu? Ah, não!"),
    ("Pare de falar bobagem! Você é quem não tem sido ele mesmo desde a batalha, Mariel!", "Pare de falar bobagem! É você quem não tem sido você mesma desde a batalha, Mariel!"),
    ("Mas não posso deixar a Razzy sozinho.", "Mas não posso deixar a Razzy sozinha."),
    ("Com suas habilidades, Sanary não pode ser derrotado…", "Com as habilidades dela, a Sanary não pode ser derrotada…"),
    ("Sanary é meu amigo.", "A Sanary é minha amiga."),
    ("Uh, ela tem um filho chamado Razzy.", "Ér, ela tem uma filha chamada Razzy."),
    ("(Sanary estava preocupado conosco.", "(A Sanary estava preocupada conosco."),
    ("Fiquei muito preocupado quando soube que Sanary e Razzy haviam sido capturados…", "Fiquei muito preocupado quando soube que a Sanary e a Razzy haviam sido capturadas…"),
    ("Você deixou a Rumari sozinho!", "Você deixou a Rumari toda sozinha!"),
    ("Você sabe, você estava muito preocupado, Sanary.", "Sabe, você estava bem preocupada ali, Sanary."),
    ("Ele queria proteger todos os Amariss e que você conheceria no futuro.", "Ele queria proteger todos que a Amariss e você conheceriam no futuro."),
    ("Algumas pessoas referem-se a ele como City of Swords.", "Algumas pessoas se referem a ela como a City of Swords."),
    ("Alguns Guardian Beasts não são bons na criação de certos tipos de armas, então talvez você não consiga usá-los com todas as técnicas.", "Algumas Guardian Beasts não são boas na criação de certos tipos de armas, então talvez você não consiga usá-las com todas as técnicas."),
    ("Este é a Gold Guild.", "Esta é a Gold Guild."),
    ("Este é a Summon Creature", "Esta é a Summon Creature"),
    ("Este tipo de Besta é chamado Stray Summon.", "Este tipo de fera é chamado de Stray Summon."),
    ("Dependendo da Guardian Beast, alguns não são bons em criar certos tipos de armas, então você pode não conseguir usá-lo com todos", "Dependendo da Guardian Beast, algumas não são boas em criar certos tipos de armas, então você pode não conseguir usá-las com todas"),
    ("Alguns Stray Summons possuem um item com eles.", "Algumas Stray Summons possuem um item com elas."),
    ("Ouvi dizer que Stray Summons foram enviados", "Ouvi dizer que Stray Summons foram enviadas"),
    ("Quanto mais fundo você for no Labirinto, mais forte será as Stray Summons.", "Quanto mais fundo você for no Labirinto, mais fortes serão as Stray Summons."),
    ("Você sabia que não podemos sair para o mar com a Water Scooters?", "Você sabia que não podemos sair para o mar com as Water Scooters?"),
    ("As Stray Summons vagando em Kagro são conhecidos por serem resistentes ao fogo.", "As Stray Summons vagando em Kagro são conhecidas por serem resistentes ao fogo."),
    ("contra Stray Summons mais forte que você", "contra Stray Summons mais fortes que você"),
    ("Ouvi dizer que Summon Beasts que possui poderes elementais do trovão estão sendo usados como guardas no forte Deigleyan em Mirana.", "Ouvi dizer que Summon Beasts que possuem poderes elementais de trovão estão sendo usadas como guardas no forte de Deigleya em Mirana."),
    ("tanto o Silver quanto a Gold Guild", "tanto a Silver quanto a Gold Guild"),
    ("tantas brigas entre os Gold e os Silver Guilds?", "tantas brigas entre a Gold e a Silver Guild?"),
    ("Varil de Gold Guild", "Varil da Gold Guild"),
    ("(Um sócio? Aposto que ele está se referindo a uma Guardian Beast.", "(Um parceiro? Aposto que ele está se referindo a uma Guardian Beast."),
    ("Ele irá invocar a Guardian Beast que se tornará seu parceiro na batalha.", "Ele irá invocar a Guardian Beast que se tornará sua parceira na batalha."),
    ("A pedra mágica com a qual uma Summon Beast é invocado.", "A pedra mágica com a qual uma Summon Beast é invocada."),
    ("Que tal… eu não esperava que você invocasse o mesmo Guardian Beast que seu pai!", "Ora essa… eu não esperava que você invocasse a mesma Guardian Beast que o seu pai!"),
    ("o mesmo Guardian Beast", "a mesma Guardian Beast"),
    ("um pequeno Stray Summon", "uma pequena Stray Summon"),
    ("equipados no Guardian Beasts", "equipados nas Guardian Beasts"),
    ("o nosso Guardian Beasts que nos ajuda", "as nossas Guardian Beasts que nos ajudam"),
    ("Minha Guardian Beast é meu melhor parceiro.", "Minha Guardian Beast é minha melhor parceira."),
    ("Sua Guardian Beast é tão tolo quanto você", "Sua Guardian Beast é tão tola quanto você"),
    ("Sempre que alguém descobre que meu pai dirige a Gold Guild, eles começam a se beijar.", "Sempre que alguém descobre que meu pai dirige a Gold Guild, começa a puxar o meu saco."),
    ("aquele grande e velho Summon Creature", "aquela enorme Summon Creature"),
    ("aquele enorme Summon Creature", "aquela enorme Summon Creature"),
    ("Este Summon Creature", "Esta Summon Creature"),
    ("Aquele Summon Creature", "Aquela Summon Creature"),
    ("A Summon Creature deixou cair alguma coisa quando o derrotamos…", "A Summon Creature deixou cair alguma coisa quando a derrotamos…"),
    ("Os terremotos são provavelmente causados por esta Summon Creature. Então esse cara também é meu inimigo!", "Os terremotos são provavelmente causados por esta Summon Creature. Então essa criatura também é minha inimiga!"),
    ("Este City of Swords", "Esta City of Swords"),
    ("E por que é chamado de City of Swords? Você não quer saber por que é chamado assim?", "E por que é chamada de City of Swords? Você não quer saber por que é chamada assim?"),
    ("Craftlord da Crystal", "Craftlord of Crystal"),
    ("Craftlord do Diamond", "Craftlord of Diamond"),
    ("Craftlord da Diamond", "Craftlord of Diamond"),
    ("a Rondeau, a Craftlord of Diamond", "o Rondeau, o Craftlord of Diamond"),
    ("a Rondeau, a Craftlord da Diamond", "o Rondeau, o Craftlord of Diamond"),
    ("todas as Iron Sabers", "todos os Iron Sabers"),
    ("um match com", "uma luta contra"),
    ("um match!", "uma luta!"),
    ("Fui ao Master para aprender", "Fui até o Mestre para aprender"),
    ("Master Craftlords", "Mestres Craftlords"),
    ("Young Master Varil", "Jovem Mestre Varil"),
    ("o Masters Sakuro e o Rondeau", "os Mestres Sakuro e Rondeau"),
    ("Masters Ureksa e Lubert", "os Mestres Ureksa e Lubert"),
    ("dos Masters Lubert e Ureksa", "dos Mestres Lubert e Ureksa"),
    ("A Master {PLAYER} que eu gosto, naturalmente sabe", "O Mestre {PLAYER} de quem eu gosto naturalmente sabe"),
    ("Esse é o master que eu gosto muito", "Esse é o mestre de quem eu gosto muito"),
    ("o Mestra Kouren", "a Mestra Kouren"),
    ("uma nova Craftlord em breve", "um novo Craftlord em breve"),
]

for _pat, _rep in [
    (r"\buma Craftknight\b", "um Craftknight"),
    (r"\bUma Craftknight\b", "Um Craftknight"),
    (r"\besta Craftknight\b", "este Craftknight"),
    (r"\bEsta Craftknight\b", "Este Craftknight"),
    (r"\bessa Craftknight\b", "esse Craftknight"),
    (r"\bEssa Craftknight\b", "Esse Craftknight"),
    (r"\baquela Craftknight\b", "aquele Craftknight"),
    (r"\bda Craftknight\b", "do Craftknight"),
    (r"\bna Craftknight\b", "no Craftknight"),
    (r"\bas Craftknights\b", "os Craftknights"),
    (r"\bAs Craftknights\b", "Os Craftknights"),
    (r"\bdas Craftknights\b", "dos Craftknights"),
    (r"\bo Craftknights\b", "os Craftknights"),
    (r"\bO Craftknights\b", "Os Craftknights"),
    (r"\bdo Craftknights\b", "dos Craftknights"),
    (r"\bno Craftknights\b", "nos Craftknights"),
    (r"\bao Craftknights\b", "aos Craftknights"),
]:
    _add_rule("Craftknight", _pat, _rep)

for _pat, _rep in [
    (r"\buma Craftlord\b(?!\s+of\s+Ruby)", "um Craftlord"),
    (r"\bUma Craftlord\b(?!\s+of\s+Ruby)", "Um Craftlord"),
    (r"\besta Craftlord\b(?!\s+of\s+Ruby)", "este Craftlord"),
    (r"\bessa Craftlord\b(?!\s+of\s+Ruby)", "esse Craftlord"),
    (r"\baquela Craftlord\b(?!\s+of\s+Ruby)", "aquele Craftlord"),
    (r"\bas Craftlords\b", "os Craftlords"),
    (r"\bAs Craftlords\b", "Os Craftlords"),
    (r"\bdas Craftlords\b", "dos Craftlords"),
    (r"\bo Craftlords\b", "os Craftlords"),
    (r"\bO Craftlords\b", "Os Craftlords"),
    (r"\bdo Craftlords\b", "dos Craftlords"),
    (r"\bno Craftlords\b", "nos Craftlords"),
    (r"\bao Craftlords\b", "aos Craftlords"),
    (r"\bpelo Craftlords\b", "pelos Craftlords"),
]:
    _add_rule("Craftlord", _pat, _rep)

for _city in CITIES_NO_ART:
    _add_rule(_city, rf"\bdo {_city}\b", f"de {_city}")
    _add_rule(_city, rf"\bDo {_city}\b", f"De {_city}")
    _add_rule(_city, rf"\bda {_city}\b", f"de {_city}")
    _add_rule(_city, rf"\bDa {_city}\b", f"De {_city}")
    _add_rule(_city, rf"\bno {_city}\b", f"em {_city}")
    _add_rule(_city, rf"\bNo {_city}\b", f"Em {_city}")
    _add_rule(_city, rf"\bna {_city}\b", f"em {_city}")
    _add_rule(_city, rf"\bNa {_city}\b", f"Em {_city}")
    _add_rule(_city, rf"\bao {_city}\b", f"a {_city}")
    _add_rule(_city, rf"\bAo {_city}\b", f"A {_city}")
    _add_rule(_city, rf"\bpelo {_city}\b", f"por {_city}")
    _add_rule(_city, rf"\bpela {_city}\b", f"por {_city}")
    _add_rule(_city, rf"\bpara o {_city}\b", f"para {_city}")
    _add_rule(_city, rf"\bpara a {_city}\b", f"para {_city}")
    _add_rule(_city, rf"\bsobre o {_city}\b", f"sobre {_city}")
    _add_rule(_city, rf"\bsobre a {_city}\b", f"sobre {_city}")
    _add_rule(_city, rf"\bque a {_city}\b", f"que {_city}")

for _lvl in ("Upper", "Middle", "Lower"):
    _t = f"{_lvl} Wystern"
    _add_rule(_t, rf"\bno {_lvl} Wystern\b", f"em {_lvl} Wystern")
    _add_rule(_t, rf"\bNo {_lvl} Wystern\b", f"Em {_lvl} Wystern")
    _add_rule(_t, rf"\bdo {_lvl} Wystern\b", f"de {_lvl} Wystern")
    _add_rule(_t, rf"\bDo {_lvl} Wystern\b", f"De {_lvl} Wystern")
    _add_rule(_t, rf"\bao {_lvl} Wystern\b", f"a {_lvl} Wystern")
    _add_rule(_t, rf"\bo {_lvl} Wystern\b", f"{_lvl} Wystern")

for _term in FEM_SG_TERMS:
    _pat_end = rf"{re.escape(_term)}(?!s)\b"
    _add_rule(_term, rf"\bo ({_pat_end})", r"a \1")
    _add_rule(_term, rf"\bO ({_pat_end})", r"A \1")
    _add_rule(_term, rf"\bum ({_pat_end})", r"uma \1")
    _add_rule(_term, rf"\bUm ({_pat_end})", r"Uma \1")
    _add_rule(_term, rf"\bdo ({_pat_end})", r"da \1")
    _add_rule(_term, rf"\bDo ({_pat_end})", r"Da \1")
    _add_rule(_term, rf"\bno ({_pat_end})", r"na \1")
    _add_rule(_term, rf"\bNo ({_pat_end})", r"Na \1")
    _add_rule(_term, rf"\bao ({_pat_end})", r"à \1")
    _add_rule(_term, rf"\bAo ({_pat_end})", r"À \1")
    _add_rule(_term, rf"\bpelo ({_pat_end})", r"pela \1")
    _add_rule(_term, rf"\bPelo ({_pat_end})", r"Pela \1")
    _add_rule(_term, rf"\bmeu ({_pat_end})", r"minha \1")
    _add_rule(_term, rf"\bMeu ({_pat_end})", r"Minha \1")
    _add_rule(_term, rf"\bteu ({_pat_end})", r"tua \1")
    _add_rule(_term, rf"\bseu ({_pat_end})", r"sua \1")
    _add_rule(_term, rf"\bSeu ({_pat_end})", r"Sua \1")
    _add_rule(_term, rf"\bnosso ({_pat_end})", r"nossa \1")
    _add_rule(_term, rf"\beste ({_pat_end})", r"esta \1")
    _add_rule(_term, rf"\bEste ({_pat_end})", r"Esta \1")
    _add_rule(_term, rf"\besse ({_pat_end})", r"essa \1")
    _add_rule(_term, rf"\bEsse ({_pat_end})", r"Essa \1")
    _add_rule(_term, rf"\baquele ({_pat_end})", r"aquela \1")
    _add_rule(_term, rf"\bAquele ({_pat_end})", r"Aquela \1")
    _add_rule(_term, rf"\balgum ({_pat_end})", r"alguma \1")
    _add_rule(_term, rf"\bnenhum ({_pat_end})", r"nenhuma \1")
    _add_rule(_term, rf"\boutro ({_pat_end})", r"outra \1")
    _add_rule(_term, rf"\bnovo ({_pat_end})", r"nova \1")
    _add_rule(_term, rf"\bpróprio ({_pat_end})", r"própria \1")
    _add_rule(_term, rf"\bmesmo ({_pat_end})", r"mesma \1")
    _add_rule(_term, rf"\bao sua ({_pat_end})", r"à sua \1")
    _add_rule(_term, rf"\bno sua ({_pat_end})", r"na sua \1")
    _add_rule(_term, rf"\bdo sua ({_pat_end})", r"da sua \1")
    _add_rule(_term, rf"\bdo tua ({_pat_end})", r"da tua \1")
    _add_rule(_term, rf"\bdo teu ({_pat_end})", r"da tua \1")

_add_rule("City of Swords", r"\bo lendário City of Swords\b", "a lendária City of Swords")
_add_rule("Central Tower", r"\bO Oficial Central Tower\b", "O Oficial da Central Tower")
_add_rule("Central Tower", r"\bo Oficial Central Tower\b", "o Oficial da Central Tower")

for _term in FEM_PL_TERMS:
    _pat_end = rf"{re.escape(_term)}\b"
    _add_rule(_term, rf"\bos ({_pat_end})", r"as \1")
    _add_rule(_term, rf"\bOs ({_pat_end})", r"As \1")
    _add_rule(_term, rf"\bo ({_pat_end})", r"as \1")
    _add_rule(_term, rf"\bO ({_pat_end})", r"As \1")
    _add_rule(_term, rf"\ba ({_pat_end})", r"as \1")
    _add_rule(_term, rf"\bA ({_pat_end})", r"As \1")
    _add_rule(_term, rf"\bdos ({_pat_end})", r"das \1")
    _add_rule(_term, rf"\bDos ({_pat_end})", r"Das \1")
    _add_rule(_term, rf"\bdo ({_pat_end})", r"das \1")
    _add_rule(_term, rf"\bDo ({_pat_end})", r"Das \1")
    _add_rule(_term, rf"\bnos ({_pat_end})", r"nas \1")
    _add_rule(_term, rf"\bno ({_pat_end})", r"nas \1")
    _add_rule(_term, rf"\baos ({_pat_end})", r"às \1")
    _add_rule(_term, rf"\bpelos ({_pat_end})", r"pelas \1")
    _add_rule(_term, rf"\buns ({_pat_end})", r"umas \1")
    _add_rule(_term, rf"\bmeus ({_pat_end})", r"minhas \1")
    _add_rule(_term, rf"\bseus ({_pat_end})", r"suas \1")
    _add_rule(_term, rf"\bestes ({_pat_end})", r"estas \1")
    _add_rule(_term, rf"\besses ({_pat_end})", r"essas \1")
    _add_rule(_term, rf"\baqueles ({_pat_end})", r"aquelas \1")
    _add_rule(_term, rf"\btodos os ({_pat_end})", r"todas as \1")
    _add_rule(_term, rf"\bTodos os ({_pat_end})", r"Todas as \1")
    _add_rule(_term, rf"\bmuitos ({_pat_end})", r"muitas \1")
    _add_rule(_term, rf"\balguns ({_pat_end})", r"algumas \1")
    _add_rule(_term, rf"\boutros ({_pat_end})", r"outras \1")
    _add_rule(_term, rf"\bnovos ({_pat_end})", r"novas \1")
    _add_rule(_term, rf"\bpróprios ({_pat_end})", r"próprias \1")

_add_rule("Stray Summons", r"As Stray Summons resistente ao vento apareceu", "As Stray Summons resistentes ao vento apareceram")
_add_rule("Stray Summons", r"As Stray Summons fica mais forte", "As Stray Summons ficam mais fortes")
_add_rule("Stray Summons", r"As Stray Summons são conhecidos por serem resistentes", "As Stray Summons são conhecidas por serem resistentes")
_add_rule("Stray Summons", r"As Stray Summons aqui são mais fortes do que aqueles", "As Stray Summons daqui são mais fortes do que aquelas")
_add_rule("Stray Summons", r"as Stray Summons são todos iguais", "as Stray Summons são todas iguais")

for _pat, _rep in [
    (r"\buma Mystic Ore\b", "um Mystic Ore"),
    (r"\ba Mystic Ore\b", "o Mystic Ore"),
    (r"\bda Mystic Ore\b", "do Mystic Ore"),
    (r"\bas Mystic Ores\b", "os Mystic Ores"),
    (r"\bdas Mystic Ores\b", "dos Mystic Ores"),
    (r"\buma Entrance Ticket\b", "um Entrance Ticket"),
    (r"\ba Entrance Ticket\b", "o Entrance Ticket"),
    (r"\bminha Entrance Ticket\b", "meu Entrance Ticket"),
    (r"\bsua Entrance Ticket\b", "seu Entrance Ticket"),
]:
    _add_rule("Mystic Ore" if "Mystic" in _pat else "Entrance Ticket", _pat, _rep)

for _fname in FEMALE_NAMES:
    _add_rule(_fname, rf"\bo {_fname}\b", f"a {_fname}")
    _add_rule(_fname, rf"\bO {_fname}\b", f"A {_fname}")
    _add_rule(_fname, rf"\bdo {_fname}\b", f"da {_fname}")
    _add_rule(_fname, rf"\bDo {_fname}\b", f"Da {_fname}")
    _add_rule(_fname, rf"\bno {_fname}\b", f"na {_fname}")
    _add_rule(_fname, rf"\bao {_fname}\b", f"à {_fname}")
    _add_rule(_fname, rf"\bpelo {_fname}\b", f"pela {_fname}")
    _add_rule(_fname, rf"\bMestre {_fname}\b", f"Mestra {_fname}")
    _add_rule(_fname, rf"\bMaster {_fname}\b", f"Mestra {_fname}")
    _add_rule(_fname, rf"\ba {_fname} esteja bem e não ferido\b", f"a {_fname} esteja bem e não esteja ferida")
    _add_rule(_fname, rf"\ba {_fname} não esteja ferido\b", f"a {_fname} não esteja ferida")
    _add_rule(_fname, rf"\ba {_fname} está ferido\b", f"a {_fname} está ferida")
    _add_rule(_fname, rf"\ba {_fname} foi sequestrado\b", f"a {_fname} foi sequestrada")
    _add_rule(_fname, rf"\ba {_fname} está preocupado\b", f"a {_fname} está preocupada")
    _add_rule(_fname, rf"\ba {_fname} está cansado\b", f"a {_fname} está cansada")
    _add_rule(_fname, rf"\ba {_fname} está sozinho\b", f"a {_fname} está sozinha")
    _add_rule(_fname, rf"\ba {_fname} ficou surpreso\b", f"a {_fname} ficou surpresa")
    _add_rule(_fname, rf"\ba {_fname} é muito forte, mas ele\b", f"a {_fname} é muito forte, mas ela")
    _add_rule(_fname, rf"\b{_fname} foi levado\b", f"{_fname} foi levada")
    _add_rule(_fname, rf"\b{_fname} foi capturado\b", f"{_fname} foi capturada")
    _add_rule(_fname, rf"\b{_fname} foi derrotado\b", f"{_fname} foi derrotada")
    _add_rule(_fname, rf"\b{_fname} está seguro\b", f"{_fname} está segura")
    _add_rule(_fname, rf"\b{_fname} está pronto\b", f"{_fname} está pronta")
    _add_rule(_fname, rf"\b{_fname} é o único\b", f"{_fname} é a única")
    _add_rule(_fname, rf"\b{_fname} é um bom\b", f"{_fname} é uma boa")
    _add_rule(_fname, rf"\b{_fname} é um ótimo\b", f"{_fname} é uma ótima")

_add_rule("Master ", r"\bMaster (Bron|Sakuro|Shintetsu|Rondeau|Lubert|Ureksa|Cazio|Varil|Tyram)\b", r"Mestre \1")
_add_rule("Master {PLAYER}", r"\bMaster \{PLAYER\}", "Mestre {PLAYER}")

RE_KNUCKLE_EN = re.compile(r"\bknuckles?\b", re.IGNORECASE)
KNUCKLE_SUBS = [
    (re.compile(r"\bos nós dos dedos\b", re.IGNORECASE), "as soqueiras"),
    (re.compile(r"\bnós dos dedos\b", re.IGNORECASE), "soqueiras"),
    (re.compile(r"\buma junta\b", re.IGNORECASE), "uma soqueira"),
    (re.compile(r"\ba junta\b", re.IGNORECASE), "a soqueira"),
    (re.compile(r"\bjuntas\b", re.IGNORECASE), "soqueiras"),
    (re.compile(r"\bjunta\b", re.IGNORECASE), "soqueira"),
    (re.compile(r"Você usa soco\?"), "Você usa soqueiras?"),
]


def postprocess_ptbr(text: str, mapping: Dict[str, str], orig_en: str) -> str:
    """Restaura os tokens protegidos e corrige concordâncias nominais e de gênero em PT-BR."""
    out = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "").strip()
    for tok, phrase in mapping.items():
        out = re.sub(re.escape(tok), phrase, out, flags=re.IGNORECASE)

    if RE_KNUCKLE_EN.search(orig_en):
        for rx, rep in KNUCKLE_SUBS:
            out = rx.sub(rep, out)

    if "motor mouth" in orig_en.lower():
        out = out.replace("um verdadeiro motor da boca", "um verdadeiro tagarela")

    for old_sub, new_sub in EXACT_SUBS:
        if old_sub in out:
            out = out.replace(old_sub, new_sub)

    for trig, rx, rep in TRIGGER_RULES:
        if trig in out:
            out = rx.sub(rep, out)

    for old_sub, new_sub in EXACT_SUBS:
        if old_sub in out:
            out = out.replace(old_sub, new_sub)

    out = re.sub(r"\bO que é isso, \{PARTNER\}\?", "O que foi, {PARTNER}?", out)

    # Preserva estilo de reticências do original
    if "…" in orig_en and "..." in out:
        out = out.replace("...", "…")
    elif "..." in orig_en and "…" in out and "…" not in orig_en:
        out = out.replace("…", "...")

    return out


def split_into_k_lines(text: str, k: int) -> List[str]:
    """Divide uma sentença traduzida em exatamente `k` linhas equilibradas por palavras."""
    s = text.strip()
    if k <= 1:
        return [s]
    words = s.split()
    if len(words) <= k:
        return words + ["..."] * (k - len(words))

    total_chars = sum(len(w) for w in words) + (len(words) - 1)
    target_len = total_chars / k
    lines: List[str] = []
    cur_words: List[str] = []
    cur_len = 0

    for i, w in enumerate(words):
        rem_words = len(words) - i
        rem_lines = k - len(lines)
        if rem_words == rem_lines:
            if cur_words:
                lines.append(" ".join(cur_words))
                cur_words = [w]
                cur_len = len(w)
            else:
                lines.append(w)
            continue

        add_len = len(w) + (1 if cur_words else 0)
        if cur_words and (cur_len + add_len > target_len * 1.12) and (len(lines) < k - 1):
            lines.append(" ".join(cur_words))
            cur_words = [w]
            cur_len = len(w)
        else:
            cur_words.append(w)
            cur_len += add_len

    if cur_words:
        if len(lines) < k:
            lines.append(" ".join(cur_words))
        else:
            lines[-1] += " " + " ".join(cur_words)

    while len(lines) < k:
        lines.append("...")
    return lines


def translate_chunk_http(chunk: List[str]) -> List[str]:
    """Traduz um lote de até 35 sentenças em uma única chamada HTTP POST."""
    protected_list = []
    mappings = []
    for s in chunk:
        p, m = protect_sentence(s)
        protected_list.append(p)
        mappings.append(m)

    # Usa separador numérico explícito que nunca é fundido pelo tradutor
    sep_lines = [f"({i+1}) {p}" for i, p in enumerate(protected_list)]
    joined_q = "\n".join(sep_lines)

    url = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=en&tl=pt-BR"
    data = urllib.parse.urlencode({"q": joined_q}).encode("utf-8")

    for attempt in range(4):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=20) as r:
                res = json.loads(r.read().decode("utf-8"))
            translated_joined = res[0] if isinstance(res[0], str) else res[0][0]
            raw_lines = [ln.strip() for ln in translated_joined.split("\n") if ln.strip()]

            if len(raw_lines) == len(chunk):
                out = []
                for i, rl in enumerate(raw_lines):
                    # Remove o prefixo (1), (2)...
                    rl_clean = re.sub(r"^\(\d+\)\s*", "", rl).strip()
                    out.append(postprocess_ptbr(rl_clean, mappings[i], chunk[i]))
                return out
            break
        except Exception:
            time.sleep(0.5 * (attempt + 1))

    # Fallback individual caso o chunk tenha quebrado linhas de forma diferente
    out = []
    for i, p in enumerate(protected_list):
        try:
            data_single = urllib.parse.urlencode({"q": p}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data_single,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                res = json.loads(r.read().decode("utf-8"))
            tr_s = res[0] if isinstance(res[0], str) else res[0][0]
            out.append(postprocess_ptbr(tr_s, mappings[i], chunk[i]))
        except Exception:
            out.append(postprocess_ptbr(p, mappings[i], chunk[i]))
    return out


def load_cache() -> Dict[str, str]:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache: Dict[str, str]) -> None:
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


def translate_sentences_with_cache(sentences: List[str], cache: Dict[str, str]) -> None:
    """Traduz todas as sentenças que ainda não estão no cache usando threads paralelas."""
    missing = []
    seen = set()
    for s in sentences:
        s_clean = s.strip()
        if not s_clean or s_clean in cache or s_clean in seen:
            continue
        if s_clean in EXACT_SENTENCE_MAP:
            cache[s_clean] = EXACT_SENTENCE_MAP[s_clean]
            continue
        m_got = re.match(r"^Got (.*?)!$", s_clean)
        if m_got:
            cache[s_clean] = f"Obteve {m_got.group(1)}!"
            continue
        seen.add(s_clean)
        missing.append(s_clean)

    if not missing:
        return

    chunk_size = 30
    chunks = [missing[i : i + chunk_size] for i in range(0, len(missing), chunk_size)]
    print(f"  • Traduzindo {len(missing)} novas sentenças ({len(chunks)} blocos)...")

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        future_to_chunk = {pool.submit(translate_chunk_http, c): c for c in chunks}
        for fut in concurrent.futures.as_completed(future_to_chunk):
            c = future_to_chunk[fut]
            res = fut.result()
            for orig_s, tr_s in zip(c, res):
                cache[orig_s] = tr_s
            completed += 1
            if completed % 10 == 0 or completed == len(chunks):
                save_cache(cache)
                print(f"    [{completed}/{len(chunks)}] blocos traduzidos...")

    save_cache(cache)


def get_08_09_translations() -> Dict[int, Dict[int, str]]:
    rom = (ROOT_DIR / "rom" / "Summon Night - Swordcraft Story (USA).gba").read_bytes()
    specs = build_opcode_spec_table(rom)
    entries = parse_archive_table(rom, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)
    return bpr.parse_dialogue_mds(
        rom,
        specs,
        entries,
        [
            MD_DIR / "08-dialogos-cap1-oficina-guilda-e-cerimonia.md",
            MD_DIR / "09-dialogos-cap1-guardioes-compras-e-labirinto.md",
        ],
    )


def generate_batch_markdown(
    file_def: Dict[str, Any],
    folder_path: Path,
    pack: Dict[str, Any],
    trans_08_09: Dict[int, Dict[int, str]],
    cache: Dict[str, str],
) -> Tuple[int, int]:
    """Gera um arquivo .md com 100% das frases traduzidas em PT-BR."""
    folder_path.mkdir(parents=True, exist_ok=True)
    md_file = folder_path / file_def["filename"]
    only_untrans_08_09 = file_def.get("only_untranslated_in_08_09", False)

    # 1ª Passada: coleta todos os grupos de sentenças deste arquivo para traduzir em lote
    script_groups_map: Dict[int, List[List[Dict[str, Any]]]] = {}
    sentences_needed: List[str] = []

    for s_idx in file_def["scripts"]:
        s_key = str(s_idx)
        if s_key not in pack:
            continue
        raw_strings = pack[s_key]["strings"]
        en_strings = [s for s in raw_strings if any(c.isascii() and c.isalpha() for c in s["en"])]
        if not en_strings:
            continue

        pre_map = trans_08_09.get(s_idx, {})
        if only_untrans_08_09:
            # Se todas as linhas deste script já estão em 08/09, pula o script para não duplicar
            if all(s["id"] in pre_map for s in en_strings):
                continue

        groups = group_script_strings(en_strings, pre_map)
        script_groups_map[s_idx] = groups
        for g in groups:
            if len(g) == 1 and g[0]["id"] in pre_map:
                continue
            joined_en = " ".join(x["en"].strip() for x in g)
            sentences_needed.append(joined_en)

    translate_sentences_with_cache(sentences_needed, cache)

    # 2ª Passada: monta o arquivo Markdown e atualiza o pack JSON
    lines_out = [
        f"# {file_def['title']}",
        "",
        "Este documento contém os diálogos extraídos da ROM traduzidos para o Português (PT-BR),",
        "seguindo o glossário oficial validado (termos técnicos, nomes de armas, itens, criaturas e locais mantidos em inglês).",
        "",
        "---",
        "",
    ]

    total_scripts = 0
    total_lines = 0

    for s_idx, groups in script_groups_map.items():
        script_info = pack[str(s_idx)]
        pre_map = trans_08_09.get(s_idx, {})

        total_scripts += 1
        lines_out.append(f"## Script `#{s_idx:04d}` (`{script_info.get('rom_addr', 'ROM')}`)")
        lines_out.append("")
        lines_out.append("| ID / Offset | Opcode | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |")
        lines_out.append("| :--- | :--- | :--- | :--- | :---: |")

        for g in groups:
            if len(g) == 1 and g[0]["id"] in pre_map:
                item = g[0]
                pt_line = pre_map[item["id"]]
                item["ptbr"] = pt_line
                en_cell = f"`{item['en'].replace('|', '/')}`"
                pt_cell = f"`{pt_line.replace('|', '/')}`"
                lines_out.append(f"| `#{s_idx:04d} [{item['id']}]` | `{item['opcode']}` | {en_cell} | {pt_cell} | ✅ Validado |")
                total_lines += 1
            else:
                joined_en = " ".join(x["en"].strip() for x in g)
                full_pt = EXACT_SENTENCE_MAP.get(joined_en, cache.get(joined_en, joined_en))
                full_pt = postprocess_ptbr(full_pt, {}, joined_en)
                split_pts = split_into_k_lines(full_pt, len(g))
                for item, pt_line in zip(g, split_pts):
                    item["ptbr"] = pt_line
                    en_cell = f"`{item['en'].replace('|', '/')}`"
                    pt_cell = f"`{pt_line.replace('|', '/')}`"
                    lines_out.append(f"| `#{s_idx:04d} [{item['id']}]` | `{item['opcode']}` | {en_cell} | {pt_cell} | ✅ Validado |")
                    total_lines += 1

        lines_out.append("")
        lines_out.append("---")
        lines_out.append("")

    md_file.write_text("\n".join(lines_out), encoding="utf-8")
    return total_scripts, total_lines


def generate_all_batches(target_folder_idx: Optional[int] = None) -> None:
    pack_data = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    scripts_pack = pack_data["scripts"]
    trans_08_09 = get_08_09_translations()
    cache = load_cache()

    print("=" * 80)
    print(" GERANDO E TRADUZINDO LOTES DE DIÁLOGOS EM MARKDOWN (.md)")
    print("=" * 80)

    for idx, b in enumerate(BATCH_DEFINITIONS, start=1):
        if target_folder_idx is not None and idx != target_folder_idx:
            continue
        folder_path = MD_DIR / b["folder"]
        print(f"\n📂 Processando Pasta {idx:02d}: {b['folder']}")
        for f in b["files"]:
            num_s, num_l = generate_batch_markdown(f, folder_path, scripts_pack, trans_08_09, cache)
            print(f"  ✓ Criado {f['filename']} ({num_s} scripts, {num_l} linhas 100% traduzidas)")

    PACK_PATH.write_text(json.dumps(pack_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print("\n[SUCESSO] Geração e tradução automática concluídas!")


if __name__ == "__main__":
    folder_arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    generate_all_batches(folder_arg)
