import json
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
GAME_DIR = os.path.dirname(BASE_DIR)
JSON_PATH = os.path.join(GAME_DIR, 'extracted', 'translation_pack_ptbr.json')
MD_DIR = os.path.join(GAME_DIR, 'ARQUIVOS md')

# 1. Update 06-itens-acessorios-materiais-e-chave.md
item_md_path = os.path.join(MD_DIR, '06-itens-acessorios-materiais-e-chave.md')
with open(item_md_path, 'r', encoding='utf-8') as f:
    item_md = f.read()

# Replace Summonite in item table
# | `0x081F4B68` / `4B8C` | `Ｂｌａｃｋｓｔｅｅｌ Ａｘｅ` | `Ａｘｅ ｆｏｒｇｅｄ ｗｉｔｈ Ｓｈｉｎｔｅｔｓｕ’ｓ ｓｏｕｌ` | `Summonite` | `Pedra para invocar {PARTNER}` |
item_md_new = re.sub(
    r"(\|\s*`0x081F4B68`\s*/\s*`4B8C`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`\s*\|\s*`)([^`]+)(`\s*\|)",
    r"\g<1>Gema de Invocação\g<3>Gema para invocar a Fera Guardiã\g<5>",
    item_md
)
if item_md_new != item_md:
    with open(item_md_path, 'w', encoding='utf-8') as f:
        f.write(item_md_new)
    print("Updated 06-itens-acessorios-materiais-e-chave.md with Gema de Invocação")

# 2. Load JSON
with open(JSON_PATH, 'r', encoding='utf-8') as f:
    pack = json.load(f)

scripts = pack['scripts']

# Explicit dictionary of script updates for Gema de Invocação and Fera Guardiã
explicit_updates = {
    # Script #1608
    ('1608', 7): 'Ele vai invocar a Fera Guardiã',
    ('1608', 8): 'que lutará ao seu lado',
    ('1608', 9): 'em batalha.',
    ('1608', 12): 'Vou ter uma Fera Guardiã',
    ('1608', 21): 'Bom… só não sei se uma',
    ('1608', 22): 'Fera Guardiã é algo que',
    ('1608', 23): 'eu deveria ter.',
    ('1608', 24): 'Não… mas não sei se uma',
    ('1608', 25): 'Fera Guardiã é algo que',
    ('1608', 26): 'eu já mereça ter.',
    ('1608', 27): 'Aprendi que só um forjador',
    ('1608', 28): 'experiente pode ter uma',
    ('1608', 29): 'Fera Guardiã.',
    ('1608', 33): 'Aceite a Fera Guardiã.',
    ('1608', 107): 'Fera Guardiã!',
    ('1608', 129): 'a sua Fera Guardiã!',
    ('1608', 154): 'invocar sua Fera Guardiã!',
    ('1608', 181): 'a sua Fera Guardiã!',
    ('1608', 263): 'Fera Guardiã que tenha',
    ('1608', 271): 'Muito bem. Agora segure',
    ('1608', 272): 'a Gema de Invocação.',
    ('1608', 273): 'Gema de Invocação? O que é isso?',
    ('1608', 274): 'A pedra mágica com a qual',
    ('1608', 275): 'se desperta uma Invocação.',
    ('1608', 277): 'e deseje uma Fera Guardiã',
    # Script #1609
    ('1609', 25): 'Ele é a Fera Guardiã que o',
    ('1609', 46): 'mesma Fera Guardiã',
    ('1609', 141): 'Olha só… não esperava que você',
    ('1609', 142): 'fosse invocar a mesma Fera',
    ('1609', 143): 'Guardiã do seu pai!',
    ('1609', 154): 'Agora que já tem sua Fera',
    ('1609', 155): 'Guardiã, siga-me até',
    ('1609', 162): 'Enfim! Já tem sua Fera Guardiã.',
    ('1609', 186): '{PARTNER} é a Fera Guardiã',
    ('1609', 187): 'que o seu pai',
    ('1609', 211): 'Fale com sua Fera Guardiã',
    # Script #208
    ('208', 19): 'Que Fera Guardiã mais fofinha!',
    # Script #221
    ('221', 22): 'Quem é a sua Fera Guardiã?',
    ('221', 24): 'O que é uma Fera Guardiã?',
    ('221', 27): 'ajuda de uma Fera Guardiã.',
    ('221', 29): 'tiver uma Fera Guardiã própria!',
    ('221', 30): 'Uma Fera Guardiã é uma criatura',
    ('221', 34): 'Hum… uma Fera Guardiã?',
    ('221', 39): 'tem uma Fera Guardiã… você',
    ('221', 43): 'com uma Fera Guardiã.',
    # Script #304
    ('304', 6): 'Sabe por que precisamos das',
    ('304', 7): 'Feras Guardiãs? Elas são',
    ('304', 8): 'parceiras inestimáveis na forja',
    ('304', 9): 'e no combate. Você pode criar',
    # Script #310
    ('310', 10): 'recuperar sua saúde. A sua',
    ('310', 11): 'Fera Guardiã também se recupera.',
    ('310', 13): 'Você conseguiu uma Fera Guardiã.',
    ('310', 14): 'A Fera Guardiã pode te apoiar',
    ('310', 15): 'na batalha com magias e itens.',
    ('310', 18): 'A Fera Guardiã não pode usar',
    ('310', 19): 'feitiços ou itens em combate a',
    ('310', 20): 'menos que estejam equipados.',
    ('310', 21): 'Uma Fera Guardiã pode equipar até',
    # Script #326
    ('326', 26): 'equipados nas Feras Guardiãs.',
    # Script #404
    ('404', 104): 'na sua Fera Guardiã.',
    # Script #410
    ('410', 15): 'da Fera Guardiã serão atualizados.',
    ('410', 18): 'que sua Fera Guardiã é',
    # Script #443
    ('443', 5): 'Feras Guardiãs não podem voltar',
    # Script #465
    ('465', 10): 'encontrar uma Fera Guardiã?',
    # Script #501
    ('501', 59): 'Fera Guardiã e como esposa.',
    # Script #504
    ('504', 70): 'Dependendo da Fera Guardiã,',
    # Script #556
    ('556', 8): 'derrotou. Foi tudo a sua Fera',
    ('556', 9): 'Guardiã! Está me ouvindo!?',
    # Script #654
    ('654', 3): 'Sua Fera Guardiã pode encantar',
    # Script #710
    ('710', 3): 'Minha Fera Guardiã é a melhor',
    # Script #756
    ('756', 4): 'Tudo graças à sua Fera Guardiã,',
    # Script #858
    ('858', 3): 'Com uma Fera Guardiã da',
    # Script #904
    ('904', 7): 'Minha Fera Guardiã pode',
    # Script #956
    ('956', 8): 'Feras Guardiãs ou amantes…',
    # Script #1568
    ('1568', 11): 'Por que a mamãe está gritando<br>sobre uma corda?',
    # Script #1604
    ('1604', 110): 'de uma Fera Guardiã. Quantos',
    # Script #1645
    ('1645', 81): 'Você era a Fera Guardiã',
    ('1645', 86): 'Você era a Fera Guardiã',
    # Script #1653
    ('1653', 6): 'por uma Fera Guardiã.',
    ('1653', 11): 'Mesmo com a sua Fera',
    ('1653', 12): 'Guardiã, não entre desarmado.',
    # Script #1659
    ('1659', 15): 'Fera Guardiã, Chaves?',
    # Script #1660
    ('1660', 24): 'Fera Guardiã!',
    # Script #1661
    ('1661', 6): 'por uma Fera Guardiã.',
    ('1661', 10): 'Mesmo com a sua Fera',
    ('1661', 11): 'Guardiã, não entre desarmado.',
    # Script #1662
    ('1662', 12): '{PARTNER} era a Fera Guardiã',
    ('1662', 44): 'a Fera Guardiã?',
    ('1662', 51): 'a Fera Guardiã do seu pai.',
    ('1662', 79): 'a Fera Guardiã do seu pai.',
    # Script #1663
    ('1663', 18): 'a Fera Guardiã do seu pai.',
    ('1663', 47): 'Vai ser a Fera Guardiã',
    ('1663', 54): 'costumava ser a Fera Guardiã',
    ('1663', 82): 'era a Fera Guardiã do seu pai.',
    # Script #1695
    ('1695', 25): 'das Feras Guardiãs, não somos',
    ('1695', 125): 'e Feras Guardiãs.',
    ('1695', 181): 'Além das nossas Feras',
    ('1695', 182): 'Guardiãs, que ajudam na luta,',
    ('1695', 187): 'e Feras Guardiãs.',
    # Script #1696
    ('1696', 23): 'Fera Guardiã.',
    # Script #1709
    ('1709', 66): 'na sua Fera Guardiã',
    ('1709', 80): 'da sua Fera Guardiã',
    ('1709', 91): 'Sua Fera Guardiã é tão tola',
    ('1709', 99): 'sua Fera Guardiã, quando é',
    # Script #1713
    ('1713', 13): 'Feras Guardiãs?',
    # Script #1757
    ('1757', 31): 'Sua Fera Guardiã',
    # Script #1799
    ('1799', 20): 'uma Fera Guardiã.',
    # Script #1851
    ('1851', 41): 'Fera Guardiã do Mestre',
    # Script #2005
    ('2005', 248): 'Eu… como a Fera Guardiã',
    ('2005', 249): 'de {PLAYER},',
    # Script #2058
    ('2058', 44): 'Aquele com a Fera Guardiã –',
    ('2058', 48): 'Aquela com a Fera Guardiã –',
    # Script #2122
    ('2122', 96): 'sua Fera Guardiã junto!',
    # Script #2125
    ('2125', 130): 'maneiras à sua Fera Guardiã…',
    # Script #2211
    ('2211', 40): 'Esta é a Gema de Invocação…',
    # Script #2213
    ('2213', 217): 'da tua Fera Guardiã.',
    # Script #2219
    ('2219', 16): 'da alma de uma Fera Guardiã,',
    ('2219', 23): 'sua Fera Guardiã.',
    # Script #2223
    ('2223', 134): 'Primeiro, a Gema de Invocação…',
    ('2223', 158): 'A alma da tua Fera Guardiã…',
    ('2223', 180): 'Eu era uma Fera Guardiã que',
    ('2223', 185): 'Eu era uma Fera Guardiã que',
    ('2223', 201): 'alma da sua Fera Guardiã?',
}

# Apply explicit updates to JSON
updated_count = 0
for (s_id, str_id), new_text in explicit_updates.items():
    if s_id in scripts:
        for e in scripts[s_id].get('strings', []):
            if e['id'] == str_id:
                if e.get('ptbr') != new_text:
                    e['ptbr'] = new_text
                    updated_count += 1

print(f"Applied {updated_count} explicit updates to translation_pack_ptbr.json")

# Save updated JSON
with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(pack, f, indent=2, ensure_ascii=False)

# 3. Synchronize all Markdown files
md_files = glob.glob(os.path.join(MD_DIR, '**', '*.md'), recursive=True)
md_synced = 0

for mdp in md_files:
    fname = os.path.basename(mdp)
    if fname.startswith(('00-', '01-', '02-', '03-', '04-', '05-', '07-')):
        continue
    with open(mdp, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content

    for (s_id, str_id), new_text in explicit_updates.items():
        s_int = int(s_id)
        pat1 = rf"(\|\s*`#{s_int:04d}\s*\[{str_id}\]`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`)"
        pat2 = rf"(\|\s*`#{s_int}\s*\[{str_id}\]`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`)"
        content = re.sub(pat1, rf"\g<1>{new_text}\g<3>", content)
        content = re.sub(pat2, rf"\g<1>{new_text}\g<3>", content)

    if content != orig:
        with open(mdp, 'w', encoding='utf-8') as f:
            f.write(content)
        md_synced += 1
        print(f"Synced MD: {os.path.relpath(mdp, GAME_DIR)}")

print(f"Total Markdown files synced: {md_synced}")
