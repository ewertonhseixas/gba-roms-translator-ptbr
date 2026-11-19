"""Check live bestiary pointers, text dimensions, race strings and preserved stats."""
import json,struct
from collections import Counter
from pathlib import Path
from toh_full_audit import rom_files
from toh_text_builder_v2 import decomp_exec,encode,CHAR_CODES
from verify_accent_fonts import Font
from toh_ui_localization import font_width

BASE=Path(__file__).resolve().parents[1]
def decode(data):
    rev={v:k for k,v in CHAR_CODES.items()};out=[];i=0
    while i<len(data):
        pair=int.from_bytes(data[i:i+2],'big')
        if pair in rev:out.append(rev[pair]);i+=2
        elif 0x81<=data[i]<=0x9f or data[i]>=0xe0:out.append(data[i:i+2].decode('cp932'));i+=2
        else:out.append(data[i:i+1].decode('cp932'));i+=1
    return ''.join(out)
def main():
    rom=(BASE/'build/Tales of Hearts - Anime Movie Edition (PT-BR).nds').read_bytes()
    files=rom_files(rom);original=rom_files((BASE/'rom/Tales of Hearts - Anime Movie Edition (EN).nds').read_bytes())
    key='btl/prm/To9_EnemyData.dat';before=original[key];after=files[key]
    font=Font(files['trialFont12.NFTR']);descs=set();samples=[]
    for index in range(372):
        at=700+index*116
        assert before[at+4:at+84]==after[at+4:at+84],index
        assert before[at+88:at+116]==after[at+88:at+116],index
        ptr=struct.unpack_from('<I',after,at+84)[0]
        text=decode(after[ptr:after.index(0,ptr)]).rstrip(' ')
        if text:
            lines=text.split('\n');assert len(lines)<=3,(index,text)
            assert all(len(s)<=35 and font_width(font,s)+len(s)<=224 for s in lines),(index,text)
            descs.add(ptr)
        if index<3:samples.append(text)
    races={0xB0480:'Incerta',0xB04C8:'Humano',0xB0868:'Cristal',0xB0B64:'Mecanoide',0xB0730:'Zerom',0xB04A8:'Alado',0xB1220:'Inseto',0xB0B70:'Aquático',0xB0880:'Réptil',0xB0518:'Planta',0xB1A94:'Fera',0xB0888:'Objeto',0xB04C0:'Dragão',0xB0890:'Amorfo',0xB06F8:'Incerta'}
    arm=decomp_exec(rom)['arm9']
    for at,text in races.items():assert arm[at:arm.index(0,at)]==encode(text),(hex(at),text)
    build=BASE/'build/validator_build_latest'
    applied=json.loads((build/'applied.json').read_text(encoding='utf8'))
    assert not json.loads((build/'blocked.json').read_text(encoding='utf8'))
    count=Counter(r['md'] for r in applied)
    for prefix,expected in [('lote-045',30),('lote-046',337),('lote-047',507)]:assert sum(n for k,n in count.items() if k.startswith(prefix))==expected
    assert any(r['source']=='m/FSHT00.B/FSHT00P.SCP' and r['offset']==0x1BFF3 and r['translation']=='......Eu...?' for r in applied)
    result={'monster_records':372,'unique_descriptions':len(descs),'max_lines':3,'max_effective_pixels':224,'stats_unchanged':True,'race_labels_verified':len(races),'short_dialogues_verified':507,'samples':samples}
    (build/'bestiary_layout_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
