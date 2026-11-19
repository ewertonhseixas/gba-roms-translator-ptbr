from pathlib import Path
import json, shutil
from toh_full_audit import rom_files
from verify_accent_fonts import Font
from toh_ui_localization import font_width
from toh_text_builder_v2 import rows_from_md

BASE=Path(__file__).resolve().parents[1]
WORK=BASE/'build/bestiary_layout_2026-11-19'
font=Font(rom_files((BASE/'build/Tales of Hearts - Anime Movie Edition (PT-BR).nds').read_bytes())['trialFont12.NFTR'])
orph=set('o a os as um uma de do da dos das em no na e ou que se por com para'.split())
def wrap(s):
    lines=[];line=[]
    for w in s.split():
        c=' '.join(line+[w])
        if line and (len(c)>35 or font_width(font,c)+len(c)>224):
            tail=[]
            while line and line[-1].lower() in orph:tail.insert(0,line.pop())
            if line:lines.append(' '.join(line))
            line=tail+[w]
        else:line.append(w)
    if line:lines.append(' '.join(line))
    return lines
def cell(s):return s.replace('|',r'\|').replace('\n','<br>').replace('\f','<page>')
def write_lot(name,title,rows):
    path=BASE/'ARQUIVOS md'/name
    text=f'# {title}\n\n| Arquivo | Offset | Texto Original (EN) | Tradução (PT-BR) | Status |\n| :--- | :--- | :--- | :--- | :---: |\n'
    text+=''.join(f'| `{src}` | `0x{off:X}` | {cell(old)} | {cell(new)} | Validado |\n' for src,off,old,new in rows)
    path.write_text(text,encoding='utf8')
    return path
if __name__=='__main__':
    data=json.loads((WORK/'descriptions_edited.json').read_text(encoding='utf8'))
    bad=[(r['name'],r['translation_text'],wrap(r['translation_text'])) for r in data if len(wrap(r['translation_text']))>3]
    print(json.dumps(bad,ensure_ascii=False,indent=2))
    if bad:raise SystemExit(1)
    source='btl/prm/To9_EnemyData.dat'
    spans=[(r['offset'],r['offset']+len(r['original'].encode('cp932'))) for r in data if r['original']]
    removals={}
    for r in rows_from_md():
        if r['md'].startswith('lote-046'):continue
        if r['source']==source and any(a<=r['offset']<b for a,b in spans):removals.setdefault(r['md'],set()).add(r['line'])
    for name,nums in removals.items():
        path=BASE/'ARQUIVOS md'/name
        backup=WORK/'backup'/name
        if not backup.exists():shutil.copy2(path,backup)
        path.write_text('\n'.join(s for n,s in enumerate(path.read_text(encoding='utf-8-sig').splitlines(),1) if n not in nums)+'\n',encoding='utf8')
    write_lot('lote-046-descricoes-do-bestiario.md','Lote 046 - Descrições do bestiário: até três linhas',[(source,r['offset'],r['original'],'\n'.join(wrap(r['translation_text']))) for r in data if r['original']])
    print('Descriptions:',sum(bool(r['original']) for r in data),'replaced fragments:',sum(map(len,removals.values())),'files:',list(removals))
