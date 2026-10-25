import json
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.dirname(BASE_DIR)
JSON_PATH = os.path.join(GAME_DIR, 'extracted', 'translation_pack_ptbr.json')
MD_DIR = os.path.join(GAME_DIR, 'ARQUIVOS md')

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    pack = json.load(f)

scripts = pack['scripts']

specific_fixes = {
    # 1. Script #1608 (Invocação - Imagens 1, 2, 3, 4, 5, 6)
    '1608': {
        7: 'Ele vai invocar a Guardiã',
        8: 'que será sua parceira',
        9: 'de batalha.',
        21: 'Bom… só não sei se uma',
        22: 'Guardiã é algo que',
        23: 'eu deveria ter.',  # Fixed copy-paste bug (Image 2)
        24: 'Não… mas não sei se uma',
        25: 'Guardiã é algo que',
        26: 'eu já mereça ter.',
        27: 'Aprendi que só um forjador',
        28: 'experiente pode ter uma',
        29: 'Guardiã.',
        33: 'Aceite a Guardiã.',
        107: 'Guardiã!',
        129: 'a sua Guardiã!',
        154: 'invocar sua Guardiã!',
        181: 'a sua Guardiã!',
        263: 'Guardiã que tenha',
        271: 'Muito bem. Agora segure',
        272: 'a pedra Summonite.',
        273: 'Pedra Summonite? O que é isso?',
        274: 'A pedra mágica com a qual',
        275: 'se desperta uma Invocação.',
        277: 'e deseje uma Guardiã',
        286: 'E agora, brada o teu nome!',
        287: 'O nome do novo laço!',
        288: 'Quem te guiará será…',
    },
    # 2. Script #1609 (Pós-Invocação - Imagem 7)
    '1609': {
        25: 'Ele é a Guardiã que o',
        46: 'mesma Guardiã',
        141: 'Olha só… não esperava que você',
        142: 'fosse invocar a mesma',
        143: 'Guardiã do seu pai!',
        154: 'Agora que você já tem sua',
        155: 'Guardiã, siga-me até',
        162: 'Enfim! Já tem sua Guardiã.',
        186: '{PARTNER} é a Guardiã',
        187: 'que o seu pai',
        211: 'Fale com sua Guardiã',
    },
    # 3. Script #0201 / #201 (Oficina - Imagem 8)
    '201': {
        15: 'Esta oficina é só para nós!',
        16: 'Não é romântico?',
        20: 'logo! Vai ser ótimo, não é?',
    },
    # 4. Script #1646 (Entrega da chave, aula, minério - Imagens 9, 10, 11, 12, 13, 14)
    '1646': {
        16: 'Aqui está sua "Chave do Labirinto".',
        21: 'Então esta é a Chave do Labirinto…',
        22: 'Esse Labirinto sob a Torre',
        23: 'Central é uma mina de tesouros',
        24: 'para os Cavaleiros.',
        38: 'Você tem que dar conta de 100 ou',
        39: '200 Errantes sem ajuda!',
        41: 'Você vai ser um Lorde, guardião',
        42: 'do Espírito Sagrado, não é?',
        127: 'Vá comprar Minério de Ferro',
        128: 'na Loja de Itens desta vez.',
        140: 'você comprar lá é que o…',
        141: '…Minério de Ferro está em promoção.',
    },
    # 5. Script #0310 / #310 (NPC Guilda - Imagem 15)
    '310': {
        10: 'recuperar a saúde. A sua Guardiã',
        11: 'também se recuperará.',
        13: 'Você conseguiu a sua Guardiã.',
        14: 'A Guardiã pode apoiá-lo na batalha',
        15: 'com feitiços e itens de suporte.',
        16: 'Claro, ela só faz isso quando',
        17: 'você der a ordem.',
        18: 'A Guardiã não pode usar feitiços',
        19: 'ou itens em combate a menos que',
        20: 'estejam equipados.',
        21: 'Uma Guardiã pode equipar até',
    },
    # 6. Script #0304 / #304 (NPC Ponte / Forja - Imagem 16)
    '304': {
        6: 'Sabe por que precisamos das',
        7: 'Guardiãs? É porque elas são',
        8: 'parceiras inestimáveis na forja',
        9: 'e no combate. Você pode criar',
        76: 'invocador por algum motivo,',
        77: 'torna-se uma Criatura Errante.',
        78: 'Também a chamam de "Errante".',
        79: 'Como eu sei de tudo isso?',
        83: 'sobre os Minérios Místicos?',
        87: 'O Minério Místico guarda um poder',
        90: 'uma arma com Minério Místico.',
        97: 'Invocações especiais no',
        98: 'Labirinto derrubam esses',
        99: 'Minérios Místicos.',
        102: 'Todo Minério Místico obtido vai',
        103: 'direto para o seu estoque.',
        114: 'com Minério Místico em materiais,',
        115: 'o Minério Místico volta para você.',
    },
    # 7. Script #0314 / #314 (NPC Quarto Espaço / Errante - Imagens 17, 18)
    '314': {
        3: 'Você já lutou com um Errante?',
        13: 'Equipamentos não valem nada se',
        14: 'você não os equipar direito.',
        15: 'Onde os equipamos?',
        16: 'No quarto espaço, claro.',
        17: 'Você também não sabe onde fica o',
        18: 'quarto espaço?',
    },
    # 8. Script #0301 / #301 (Loja de Itens / Promoção de Ferro)
    '301': {
        18: 'de Itens! O minério vai esgotar!',
        19: 'Promoção de Minério de Ferro♪',
        45: 'O Minério de Ferro acabou.',
    },
    # 9. Script #0404 / #404 (Mystic Ore & Errante)
    '404': {
        12: 'Você tem "Minério Místico"?',
        33: 'Seu ataque não afetará um',
        34: 'Errante se ele usar o mesmo',
        35: 'elemento de sua arma.',
        75: 'eu sei sobre o Minério Místico?',
        79: 'Minério Místico é uma pedra que',
        81: 'Se usar o Minério Místico',
        90: 'Existem Invocações',
        91: 'no Labirinto que possuem',
        92: 'o Minério Místico…',
        95: 'Se achar Minério Místico, ele vai',
        100: 'Vou lhe dar três Minérios Místicos',
        102: 'O Minério Místico só serve para',
        106: 'usa Minério Místico e desmontá-la',
        108: 'você recuperará o Minério Místico',
        111: 'a arma, o Minério Místico será',
    },
    # 10. Script #0504 / #504 (Mystic Ore & Invocações)
    '504': {
        46: 'sobre o Minério Místico?',
        50: 'O Minério Místico tem um poder',
        53: 'em algo especial com esse minério.',
        60: 'Uma Invocação especial',
        61: 'no Labirinto possui isso.',
        63: 'Assim, esse minério é raríssimo.',
        70: 'Dependendo da Guardiã,',
        76: 'Minério Místico em materiais,',
        77: 'você receberá o minério de volta.',
    },
    # 11. Script #0554 / #554 (Mystic Ore)
    '554': {
        1: 'usando Minério Místico! Segui as',
        3: 'adicionei Minério Místico à arma.',
    },
    # 12. Script #0556 / #556 (Guardian Beast)
    '556': {
        8: 'derrotou. Foi tudo a sua',
        9: 'Guardiã! Você está me ouvindo!?',
    },
    # 13. Script #0704 / #704 (Invocações)
    '704': {
        24: 'Mas parece que outras',
        25: 'Invocações entraram por lá…',
    },
    # 14. Script #0750 / #750 (Invocações)
    '750': {
        6: 'informações sobre todas as',
        7: 'Invocações que conheceu antes',
    },
    # 15. Script #0754 / #754 (Errantes)
    '754': {
        7: 'Errantes que encontrar.',
        8: 'As informações sobre os',
        9: 'Errantes são muito valiosas.',
    },
    # 16. Script #0865 / #865 (Errante & pra)
    '865': {
        1: 'Dá para arremessar um',
        2: 'Errante pequeno para longe dele.',
    },
    # 17. Script #0915 / #915 (Errantes)
    '915': {
        13: 'alguns Errantes no Kagro Volcano.',
    },
    # 18. Script #0954 / #954 (Errantes)
    '954': {
        1: 'lutar com Errantes mais fortes."',
    },
    # 19. Script #1104 / #1104 (Errantes)
    '1104': {
        27: 'duzentos Errantes com minha',
    },
    # 20. Script #1115 / #1115 (Invocações)
    '1115': {
        19: 'Ouvi dizer que Invocações',
    },
    # 21. Script #1550 / #1550 (Invocações)
    '1550': {
        16: 'bestiário de todas as Invocações.',
    },
    # 22. Script #1955 / #1955 (Invocações)
    '1955': {
        52: 'Que Invocação tão estranha!',
        56: 'Que Invocação tão fofa.',
        100: 'Que Invocação tão estranha!',
        104: 'Que Invocação tão charmosa.',
        131: 'Que Invocação tão estranha!',
        135: 'Que Invocação tão fofa!',
        173: 'Que bela Invocação.',
        175: 'Ele é uma Invocação viril…',
        177: 'Que Invocação charmosa.',
    },
    # 23. Script #2005 / #2005 (Guardiã)
    '2005': {
        248: 'Eu… como a Guardiã',
        249: 'de {PLAYER},',
    },
    # 24. Script #2211 / #2211 (pedra Summonite)
    '2211': {
        40: 'Esta é uma pedra Summonite…',
    },
    # 25. Script #2212 / #2212 (Invocações)
    '2212': {
        89: 'com a ajuda de Invocações',
    },
    # 26. Script #2213 / #2213 (minério Summonite)
    '2213': {
        73: 'minério Summonite.',
        77: 'feitos de minério Summonite…',
        106: 'Este é o minério Summonite.',
        217: 'da tua Guardiã.',
    },
    # 27. Script #2219 / #2219 (Guardiã)
    '2219': {
        16: 'da alma de uma Guardiã,',
        23: 'sua Guardiã.',
    },
    # 28. Script #2223 / #2223 (Guardiã & Summonite)
    '2223': {
        134: 'Primeiro, a pedra Summonite…',
        145: 'Minério Summonite…',
        158: 'A alma da tua Guardiã…',
        180: 'Eu era uma Guardiã que',
        185: 'Eu era uma Guardiã que',
        201: 'alma da sua Guardiã?',
    },
    # 29. Script #0459, #0601, #0853, #1763, #2201 (Torre Central)
    '459': {
        1: 'dia de folga. A equipe da Torre',
        2: 'Central tem estado muito ocupada',
    },
    '601': {
        68: 'A casa dele fica na Torre Central.',
        69: 'Lá no segundo andar, certo?',
    },
    '853': {
        6: 'informaria a Torre',
        7: 'Central sobre o homem.',
        9: 'informaria a Torre',
        10: 'Central sobre o homem.',
    },
    '1763': {
        11: 'O quarto andar da Torre',
        12: 'Central? Eu nunca estive lá…',
    },
    '2201': {
        33: 'outra entrada na Torre',
        34: 'Central que leva ao Labirinto.',
    }
}

# 1. Update JSON with specific fixes
for s_id, fixes in specific_fixes.items():
    if s_id in scripts:
        s_data = scripts[s_id]
        for e in s_data.get('strings', []):
            if e['id'] in fixes:
                e['ptbr'] = fixes[e['id']]

# 2. General cleanup in JSON
skip_scripts_guardia = {'1604', '221'}
for s_id, s_data in scripts.items():
    if s_id in skip_scripts_guardia:
        continue
    for e in s_data.get('strings', []):
        pt = e.get('ptbr', '')
        if not pt:
            continue
        new_pt = pt
        if 'Fera Guardiã' in new_pt:
            new_pt = new_pt.replace('Fera Guardiã', 'Guardiã')
        if 'fera guardiã' in new_pt:
            new_pt = new_pt.replace('fera guardiã', 'guardiã')
        if 'Feras Guardiãs' in new_pt:
            new_pt = new_pt.replace('Feras Guardiãs', 'Guardiãs')
        if 'feras guardiãs' in new_pt:
            new_pt = new_pt.replace('feras guardiãs', 'guardiãs')
        if 'né?' in new_pt:
            cand = new_pt.replace('né?', 'não é?')
            if len(cand) <= 35:
                new_pt = cand
            else:
                cand2 = re.sub(r'\s*,?\s*né\?', ', certo?', new_pt)
                if len(cand2) <= 35:
                    new_pt = cand2
        if len(new_pt) <= 35:
            e['ptbr'] = new_pt

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(pack, f, indent=2, ensure_ascii=False)

print("Updated translation_pack_ptbr.json successfully.")

# 3. Update all Markdown files to match!
md_files = glob.glob(os.path.join(MD_DIR, '**', '*.md'), recursive=True)
md_updated_count = 0

for mdp in md_files:
    fname = os.path.basename(mdp)
    if fname.startswith(('00-', '01-', '02-', '03-', '04-', '05-', '06-', '07-')):
        continue
    with open(mdp, 'r', encoding='utf-8') as f:
        content = f.read()
    orig_content = content

    # Apply specific string replacements in markdown tables
    # Patterns like: | `#1608 [23]` | Cleru | `...` | `OLD` |
    # or `| `+0x...` | Sugar | `...` | `OLD` |
    for s_id, fixes in specific_fixes.items():
        s_int = int(s_id)
        for str_id, new_text in fixes.items():
            pattern1 = rf"(\|\s*`#{s_int:04d}\s*\[{str_id}\]`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`)"
            pattern2 = rf"(\|\s*`#{s_int}\s*\[{str_id}\]`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`)"
            content = re.sub(pattern1, rf"\g<1>{new_text}\g<3>", content)
            content = re.sub(pattern2, rf"\g<1>{new_text}\g<3>", content)

    # Specific manual text replacements for lines with offset headers (like Script 0201 in 08-dialogos)
    if '08-dialogos-cap1-oficina-guilda-e-cerimonia.md' in mdp:
        content = content.replace(
            "`Esta oficina é só para nós`<br>`dois! Não é romântico?`",
            "`Esta oficina é só para nós!`<br>`Não é romântico?`"
        )
        content = content.replace(
            "`Nossa oficina vai ficar pronta`<br>`logo! Vai ser ótimo, né?`",
            "`Nossa oficina vai ficar pronta`<br>`logo! Vai ser ótimo, não é?`"
        )

    # General replacements across dialogue MDs (avoiding 1604 and 221)
    if '1604' not in mdp and '0221' not in mdp and '221' not in mdp:
        content = content.replace('Fera Guardiã', 'Guardiã')
        content = content.replace('fera guardiã', 'guardiã')
        content = content.replace('Feras Guardiãs', 'Guardiãs')
        content = content.replace('feras guardiãs', 'guardiãs')

    if content != orig_content:
        with open(mdp, 'w', encoding='utf-8') as f:
            f.write(content)
        md_updated_count += 1
        print(f"Updated MD: {os.path.relpath(mdp, GAME_DIR)}")

print(f"Total Markdown files updated: {md_updated_count}")
