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

replacements_44 = {
    ('250', 4): 'Sou desajeitado para ferreiro.',
    ('401', 3): 'O Mestre Bron nos espera lá.',
    ('415', 12): 'força para destruir armas rivais!',
    ('555', 0): 'Está rindo do meu nome!? Meus',
    ('601', 92): 'Nunca se sabe o que ele pensa…',
    ('658', 0): 'Minha esposa está na oficina',
    ('710', 28): 'Está quente, e eu sei',
    ('1001', 89): 'A verdade é que eu queria só nós.',
    ('1162', 5): 'quando ele levantar. Legal, não?',
    ('1310', 0): 'No estado em que está, não posso',
    ('1568', 11): 'Por que a mamãe está gritando<br>sobre uma corda?',
    ('1601', 19): 'Está brincando!? Claro que não!',
    ('1603', 4): 'Por que está parado desse jeito!?',
    ('1608', 257): 'Tudo bem, Mestre!',
    ('1609', 95): 'O que foi? Está olhando o quê?',
    ('1609', 132): 'Tudo bem! Sigam-me até',
    ('1610', 7): 'Está brincando!?',
    ('1646', 144): 'Está custando 10 boam cada!!',
    ('1646', 145): 'Está muito barato!',
    ('1654', 6): 'Tudo bem, que seja.',
    ('1701', 18): 'Ah! Está resmungando por',
    ('1701', 120): 'Tudo bem. Pare de choramingar',
    ('1712', 27): 'Não dá para lutar com tudo',
    ('1761', 0): 'Atrasou, {SIBLING}! Lembre-se,',
    ('1764', 2): 'Dá para subir ao quarto andar!',
    ('1797', 17): 'Está brincando comigo!?',
    ('1802', 3): 'Sem um caminho para descer,',
    ('1803', 2): 'Entendi. Está buscando a chave…',
    ('1810', 215): '12ºA do Labirinto. Precisa disso',
    ('1812', 0): 'A arma da luta está pronta?',
    ('1850', 110): 'Me diga o que ele está pensando!',
    ('1854', 9): 'Demora para notar as coisas!',
    ('1921', 20): 'Cheio de confiança, não é?',
    ('1959', 25): 'Nem consegue responder, não é?',
    ('2000', 170): 'Está me dizendo que é garota?!',
    ('2024', 14): 'Hein? Está tramando algo de novo?',
    ('2106', 5): 'Não está me tratando bem…',
    ('2107', 61): 'me salvar. E ainda ouve tudo.',
    ('2107', 80): 'Sanary, você dá o seu melhor!',
    ('2113', 107): 'Tudo bem. Pare de empurrar.',
    ('2162', 59): 'É a irmã mais velha dela, não é?',
    ('2213', 157): 'Hã!? Agradece por não',
    ('2348', 13): 'Quer dizer que gosto de você.',
    ('2348', 23): 'Certo, mas tenho outro sonho!',
}

# Apply to JSON
for (s_id, str_id), new_text in replacements_44.items():
    if s_id in scripts:
        for e in scripts[s_id].get('strings', []):
            if e['id'] == str_id:
                e['ptbr'] = new_text

with open(JSON_PATH, 'w', encoding='utf-8') as f:
    json.dump(pack, f, indent=2, ensure_ascii=False)

print("Applied 44 replacements to translation_pack_ptbr.json")

# Also update corresponding Markdown files
md_files = glob.glob(os.path.join(MD_DIR, '**', '*.md'), recursive=True)
count_md_repl = 0
for mdp in md_files:
    fname = os.path.basename(mdp)
    if fname.startswith(('00-', '01-', '02-', '03-', '04-', '05-', '06-', '07-')):
        continue
    with open(mdp, 'r', encoding='utf-8') as f:
        content = f.read()
    orig = content
    for (s_id, str_id), new_text in replacements_44.items():
        s_int = int(s_id)
        pat1 = rf"(\|\s*`#{s_int:04d}\s*\[{str_id}\]`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`)"
        pat2 = rf"(\|\s*`#{s_int}\s*\[{str_id}\]`\s*\|[^|]*\|[^|]*\|\s*`)([^`]+)(`)"
        content = re.sub(pat1, rf"\g<1>{new_text}\g<3>", content)
        content = re.sub(pat2, rf"\g<1>{new_text}\g<3>", content)
    if content != orig:
        with open(mdp, 'w', encoding='utf-8') as f:
            f.write(content)
        count_md_repl += 1
        print(f"Updated MD: {os.path.relpath(mdp, GAME_DIR)}")

print(f"Updated {count_md_repl} markdown files.")
