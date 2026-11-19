"""Create bounded, traceable Markdown batches from verified insertion records."""
from collections import defaultdict, Counter
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from toh_full_audit import rom_files, fps4, unpack
from verify_accent_fonts import Font
from toh_text_builder_v2 import CHAR_CODES, rows_from_md

BASE = Path(__file__).resolve().parents[1]
WORK = BASE / 'build/validator_reorganization_audit'
ORPHANS = {'o','a','os','as','um','uma','de','do','da','dos','das','em','no','na',
           'e','ou','que','se','por','com','para','ao','à'}
ADVANCES = {}


def md(text):
    return text.replace('|', r'\|').replace('\f', '<page>').replace('\n', '<br>')


def visible(text):
    return re.sub(r'\(?[SBC]\d{6}\)', '', text)


def pixel_width(text, font):
    width = 0
    for c in visible(text):
        if c in CHAR_CODES:
            cp = CHAR_CODES[c]
        else:
            raw = c.encode('cp932')
            cp = int.from_bytes(raw, 'big')
        key = id(font), cp
        if key not in ADVANCES:
            try:
                ADVANCES[key] = font.cell_for(cp)[1][2]
            except ValueError:
                ADVANCES[key] = font.width
        width += ADVANCES[key]
    return width


def wrap(text, font, limit=32, max_pixels=210):
    result = []
    for page in text.split('\f'):
        # Keep explicit page boundaries, reflow only the words inside a page.
        words = page.split()
        lines = []
        while words:
            line = []
            while words and (not line or (len(' '.join(line + words[:1])) <= limit
                             and pixel_width(' '.join(line + words[:1]), font) <= max_pixels)):
                line.append(words.pop(0))
            if words:
                while len(line) > 1 and line[-1].lower() in ORPHANS:
                    words.insert(0, line.pop())
            value = ' '.join(line)
            if len(value) > 35 or pixel_width(value, font) > 224:
                raise ValueError(f'Unbreakable text exceeds display bounds: {value!r}')
            lines.append(value)
        result.append('\n'.join(lines))
    return '\f'.join(result)


def two_lines(text, font):
    words = text.split()
    if len(text) <= 35 and pixel_width(text, font) <= 210:
        return text
    choices = []
    for i in range(1, len(words)):
        a, b = ' '.join(words[:i]), ' '.join(words[i:])
        if max(len(a), len(b)) <= 35 and max(pixel_width(a, font), pixel_width(b, font)) <= 210:
            if words[i-1].lower() not in ORPHANS:
                choices.append((max(len(a), len(b)), abs(len(a)-len(b)), a+'\n'+b))
    if not choices:
        raise ValueError(f'Description needs editorial shortening: {text}')
    return min(choices)[2]


def main():
    stage = WORK / 'staged_md'
    stage.mkdir(exist_ok=True)
    # Only remove derived batches inside this staging directory on a rerun.
    for previous in stage.glob('lote-*.md'):
        previous.unlink()
    evidence = BASE / 'build/accent_fix_2026-11-18'
    applied = json.loads((evidence / 'applied.json').read_text('utf-8'))
    live = {(r['md'], r['line']): r for r in rows_from_md()}
    for row in applied:
        current = live.get((row['md'], row['line']))
        if current is None or any(current[k] != row[k] for k in ('source','offset','original')):
            raise ValueError('Source metadata changed since verified build: ' + str((row['md'],row['line'])))
        row['translation'] = current['translation']
    original_files = rom_files((BASE / 'rom/Tales of Hearts - Anime Movie Edition (EN).nds').read_bytes())
    final_files = rom_files((BASE / 'build/Tales of Hearts - Anime Movie Edition (PT-BR).nds').read_bytes())
    font = Font(final_files['trialFont12.NFTR'])
    outer = {n:d for n,_,_,_,d in fps4(original_files['m/m.b'], original_files['m/m.dat'])}
    intro = next(unpack(d)[0] for n,_,_,_,d in fps4(outer['FSHT00.B'], outer['FSHT00.MAPBIN'])
                 if n == 'FSHT00P.SCP')
    repairs = []
    for at, pt in [(0x1b8d1, "Escute, Shing|. Treine 'aqui' acima de tudo."),
                   (0x1ba7c, 'Shing|, crio você para ter uma Spiria forte de verdade, sem se abalar por emoções.')]:
        end = intro.index(b'\0', at)
        repairs.append(dict(source='m/FSHT00.B/FSHT00P.SCP', offset=at,
                            original=intro[at:end].decode('ascii').rstrip(), translation=pt))
    rows, removed = [], []
    for row in applied:
        source, offset = row['compiled_source'], row['resolved_offset']
        if any(source == r['source'] and offset < r['offset'] + len(r['original'])
               and r['offset'] < offset + len(row['original'].encode('cp932')) for r in repairs):
            removed.append(row)
            continue
        rows.append(dict(source=source, offset=offset, original=row['original'],
                         translation=row['translation'], box=row['string_start'],
                         origin=f"{row['md']}:{row['line']}"))
    for row in repairs:
        rows.append(dict(row, box=row['offset'], origin='Reparo de tabela da introdução'))
    # All additional named-item entries come from proven table pointers.
    translations = {}
    for line in (BASE / 'tools/toh_remaining_tables_ptbr.tsv').read_text('utf-8').splitlines():
        key, name, description = line.split('|', 2)
        if key in translations:
            raise ValueError('Duplicate table translation: ' + key)
        translations[key] = name, description
    records = json.loads((WORK / 'item_records.json').read_text('utf-8'))
    for record in records:
        name, desc = translations[record['id']]
        if len(name) > 35 or pixel_width(name, font) > 184:
            raise ValueError('Item name exceeds reviewed width: ' + name)
        desc = two_lines(desc, font)
        for field, pt in [('name', name), ('description', desc)]:
            item = record[field]
            rows.append(dict(source=record['source'], offset=item['offset'],
                             original=item['original'], translation=pt, box=record['name']['offset'],
                             origin=record['id']+'/'+field, table_field=field))
    if set(translations) != {r['id'] for r in records}:
        raise ValueError('Table translation coverage mismatch')
    candidates = json.loads((WORK / 'untranslated_direct_candidates.json').read_text('utf-8'))
    for candidate in candidates:
        if candidate['source'] == 'item/TODS9_ValueData.dat' and candidate['original'] in ('Recipe','Gummila','Battery'):
            rows.append(dict(source=candidate['source'],offset=candidate['offset'],
                             original=candidate['original'],
                             translation={'Recipe':'Receita','Gummila':'Gummila','Battery':'Bateria'}[candidate['original']],
                             box=candidate['offset'],origin='Revisão de itens-chave',table_field='name'))
    for row in rows:
        if not row.get('table_field'):
            pt = visible(row['translation'])
            if row['source'].startswith('m/'):
                for a,b in [(r'\bvc\b','você'),(r'\btb\b','também'),(r'\bpq\b','porque'),
                            (r'\bq\b','que'),(r'\batq\.','ataque'),(r'\besp\.','especial')]:
                    pt = re.sub(a,b,pt,flags=re.I)
            row['translation'] = wrap(pt, font)
        if not row['translation'].strip():
            raise ValueError('Empty translation')
    groups = defaultdict(list)
    for row in rows:
        groups[row['source'], row['box']].append(row)
    def order(key):
        source, box = key
        return (0 if 'FSHT00' in source else 1 if source.startswith('m/') else 2, source, box)
    batches, lines, content, sources = [], [], [], set()
    section = None
    def flush():
        nonlocal lines, content, sources, section
        if not content:
            return
        number = len(batches) + 1
        first = content[0]['source']
        if number == 1:
            label, slug = 'Introdução — sonho e treino / FSHT00', 'dialogos-introducao-fsht00'
        elif first.startswith('m/'):
            code = first.split('/')[1][:-2].lower()
            label, slug = 'Diálogos — mapas ' + ', '.join(sorted(s.split('/')[1][:-2] for s in sources)), 'dialogos-mapas-'+code
        else:
            label, slug = 'Sistema e itens — ' + Path(first).stem, 'sistema-itens-'+Path(first).stem.lower()
        name = f'lote-{number:03d}-{slug}.md'
        text = f'# Lote {number:03d} — {label}\n\n'
        text += 'Revisão técnica de largura e sintaxe; confirmação visual em jogo ainda necessária.\n\n'
        text += '\n'.join(lines) + '\n'
        if len(text.splitlines()) > 1000:
            raise ValueError('Batch exceeds 1000 physical lines')
        (stage/name).write_text(text,'utf-8')
        batches.append(dict(filename=name, title=label, rows=len(content), lines=len(text.splitlines()),
                            sources=sorted(sources), first_source=first,
                            first_offset=content[0]['offset'], last_offset=content[-1]['offset']))
        lines, content, sources, section = [], [], set(), None
    for key in sorted(groups, key=order):
        source = key[0]
        group = sorted(groups[key], key=lambda r:r['offset'])
        header = []
        if section != source:
            header = ['', '## '+source, '',
                      '| Arquivo | Offset | Texto Original (EN) | Tradução (PT-BR) | Status | Caixa |',
                      '| :--- | :--- | :--- | :--- | :---: | :--- |']
        # Never split the fragments belonging to the same original text box.
        if content and (len(lines) + len(header) + len(group) + 5 > 1000
                        or (content[0]['source'].startswith('m/') != source.startswith('m/'))
                        or (('FSHT00' in content[0]['source']) != ('FSHT00' in source))):
            flush()
            header = ['', '## '+source, '',
                      '| Arquivo | Offset | Texto Original (EN) | Tradução (PT-BR) | Status | Caixa |',
                      '| :--- | :--- | :--- | :--- | :---: | :--- |']
        lines.extend(header)
        section = source
        sources.add(source)
        for row in group:
            lines.append(f"| `{source}` | `0x{row['offset']:X}` | {md(row['original'])} | {md(row['translation'])} | Revisão técnica | 0x{row['box']:X} |")
            content.append(row)
    flush()
    for name in ['02-glossario-e-terminologias.md','catalogo-de-personagens.md']:
        shutil.copy2(BASE/'ARQUIVOS md'/name,stage/name)
    index = ['# Índice — Tales of Hearts', '',
             'Cada lote tem até 1.000 linhas físicas. As seções mantêm o pacote e o script originais.', '',
             'A ordem dos códigos de mapas não é uma afirmação sobre capítulos narrativos.', '',
             '| Lote | Contexto | Recursos / scripts | Entradas | Linhas |', '| :--- | :--- | :--- | ---: | ---: |']
    for b in batches:
        index.append(f"| [{b['filename']}]({b['filename']}) | {b['title']} | {', '.join(b['sources'])} | {b['rows']} | {b['lines']} |")
    index += ['', 'Os dados brutos e os arquivos antigos estão preservados no backup em build/validator_reorganization_audit.',
              'Cobertura desta revisão: traduções previamente inseridas, duas falas recuperadas e cinco tabelas de itens.',
              'Isso não certifica textos ainda não extraídos, textos em imagens ou todas as cenas do jogo.']
    (stage/'00-indice.md').write_text('\n'.join(index)+'\n','utf-8')
    provenance = dict(source_build=str(evidence), previous_applied=len(applied),
                      replacement_fragments=len(removed), intro_repairs=len(repairs),
                      added_table_records=len(records), active_rows=len(rows), batches=batches)
    (WORK/'reorganization.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(f'Generated {len(batches)} batches; {len(rows)} rows; max {max(b["lines"] for b in batches)} lines.')


if __name__ == '__main__':
    main()
