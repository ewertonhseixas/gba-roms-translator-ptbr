"""Reproducible UI graphics and whole-page OTLE synopsis localization."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import struct

from toh_ui_graphics import BASE, OUT, localize_graphics
from toh_full_audit import rom_files
from toh_text_builder_v2 import decomp_exec, encode, write_rom, CHAR_CODES
from verify_accent_fonts import Font
from toh_movie_guard import audit_movie


def read_synopsis():
    # Chapters 8 and 24 have two pages; the EN third-page pointers alias later chapters.
    pages={(8,3):[],(24,3):[]};titles={}
    for path in sorted((BASE/'ARQUIVOS md').glob('sinopse-*.md')):
        for line in path.read_text(encoding='utf8').splitlines():
            cells=re.split(r'(?<!\\)\|',line)
            if len(cells)<6:continue
            key=cells[1].strip();value=cells[4].strip()
            match=re.fullmatch(r'S(\d+)(T|P([123]))',key)
            if not match:continue
            chapter=int(match[1])
            if match[2]=='T':
                assert chapter not in titles
                titles[chapter]=value
            else:
                pair=(chapter,int(match[3]));assert pair not in pages
                pages[pair]=value.split('<br>') if value else []
    assert len(pages)==144 and len(titles)==48
    return pages,titles


def font_width(font,value):
    width=0
    for ch in value:
        cp=CHAR_CODES.get(ch)
        if cp is None:cp=int.from_bytes(ch.encode('cp932'),'big')
        width+=font.cell_for(cp)[1][2]
    return width


def highlight(line):
    # Each NUL-delimited line is independently balanced; color cannot leak to the next line.
    terms=r'Floresta de Espinhos|Mundo Cristalino|Elo de Spiria|Elo de Soma|Spirunas?|Spiria|Despir|Soma'
    return re.sub(r'\b('+terms+r')\b',lambda m:'\x03(3)'+m[0]+'\x03(0)',line)


def build_synopsis(original,files):
    pages,titles=read_synopsis();font=Font(files['trialFont10.NFTR'])
    pool=0x30+49*24
    assert original[:4]==b'OTLE' and struct.unpack_from('<H',original,4)[0]==49
    out=bytearray(original[:pool]);report=[]
    # Ten actor-name pointers precede the 49 fixed-size records.
    for at in range(8,0x30,4):
        old=struct.unpack_from('<I',original,at)[0]
        name=original[old:original.index(0,old)]
        struct.pack_into('<I',out,at,len(out));out.extend(name+b'\0')
    for chapter in range(1,49):
        record=0x30+chapter*24
        title=titles[chapter]
        assert '\n' not in title and len(title)<=35
        assert font_width(font,title)<=200,(chapter,title)
        struct.pack_into('<I',out,record+8,len(out));out.extend(encode(title)+b'\0')
        for page in range(1,4):
            lines=pages[chapter,page]
            assert len(lines)<=8,(chapter,page,len(lines))
            out[record+4+page]=len(lines)
            struct.pack_into('<I',out,record+8+page*4,len(out))
            if not lines:out.append(0)
            for line in lines:
                assert 0<len(line)<=35,(chapter,page,line)
                assert font_width(font,line)<=224,(chapter,page,line)
                assert not any(c in line for c in '\n\f\0')
                out.extend(encode(highlight(line))+b'\0')
            report.append(dict(chapter=chapter,page=page,lines=len(lines)))
    # Record zero is an unused placeholder with interior aliases into the first page.
    first=struct.unpack_from('<I',out,0x30+24+12)[0]
    for i in range(4):struct.pack_into('<I',out,0x30+8+i*4,first+3+i)
    assert out[0x30:0x38]==original[0x30:0x38]
    verify_synopsis(bytes(out),pages,titles)
    return bytes(out),report


def verify_synopsis(data,pages,titles):
    for chapter in range(1,49):
        record=0x30+chapter*24
        pt=struct.unpack_from('<I',data,record+8)[0]
        assert data[pt:data.index(0,pt)]==encode(titles[chapter])
        for page in range(1,4):
            lines=pages[chapter,page]
            assert data[record+4+page]==len(lines)
            pt=struct.unpack_from('<I',data,record+8+page*4)[0]
            for expected in lines:
                end=data.index(0,pt);raw=data[pt:end]
                assert raw==encode(highlight(expected))
                assert b'\n' not in raw and b'\x0c' not in raw
                assert raw.count(b'\x03(3)')==raw.count(b'\x03(0)')
                pt=end+1


def patch_labels(rom):
    executables=decomp_exec(rom);changed={};report=[]
    arm=bytearray(executables['arm9']);at=0xb045c
    if arm[at:at+8]==b'New\0No.\0':
        # Both adjacent labels occupy eight bytes. Replace the number abbreviation
        # with #, allowing Novo in the same space without moving executable data.
        arm[at:at+8]=b'Novo\0#\0\0'
        ram=struct.unpack_from('<I',rom,0x28)[0]
        old=struct.pack('<I',ram+at+4);new=struct.pack('<I',ram+at+5)
        refs=[i for i in range(0,len(arm)-3,4) if arm[i:i+4]==old]
        assert refs,'Missing adjacent number-label references'
        for i in refs:arm[i:i+4]=new
        changed['arm9']=bytes(arm)
    else:assert arm[at:at+5]==b'Novo\0'
    report.append(dict(resource='arm9',offset=hex(at),text='Novo'))
    offsets={'ov_03':[0x5edd8,0x5fa68,0x5fa7c],'ov_22':[0x68c0],'ov_30':[0x40b4]}
    for key,positions in offsets.items():
        data=bytearray(executables[key]);modified=False
        for at in positions:
            old=b'Seable Village';new=b'Vila Seable'
            if data[at:at+len(old)]==old:
                data[at:at+len(old)]=new.ljust(len(old),b'\0');modified=True
            else:assert data[at:at+len(new)]==new,(key,hex(at))
            report.append(dict(resource=key,offset=hex(at),text='Vila Seable'))
        if modified:changed[key]=bytes(data)
    return changed,report


def apply(input_path,output_path,report_dir=OUT):
    rom=input_path.read_bytes();files=rom_files(rom)
    original=rom_files((BASE/'rom/Tales of Hearts - Anime Movie Edition (EN).nds').read_bytes())
    replacements,graphics=localize_graphics(files,report_dir)
    synopsis,synopsis_report=build_synopsis(original['TODS3_OutLineData.dat'],files)
    replacements['TODS3_OutLineData.dat']=synopsis
    movie_manifest=BASE/'tools/movie_compatibility.json'
    if movie_manifest.exists():
        for name,entry in json.loads(movie_manifest.read_text(encoding='utf8')).items():
            asset=(BASE/entry['asset']).read_bytes()
            assert hashlib.sha256(asset).hexdigest()==entry['sha256']
            if files[name]!=asset:replacements[name]=asset
    movie_report={name:audit_movie(replacements.get(name,data)) for name,data in files.items()
                  if name.startswith('movie/') and name.endswith('.mods')}
    # This raw location table is also used by the Spirlink interface.
    key='TODS3_SpirLinkData.dat'
    data=files[key];old=b'Seable Village';new=b'Vila Seable'
    if old in data:replacements[key]=data.replace(old,new.ljust(len(old),b'\0'))
    exec_changes,labels=patch_labels(rom)
    write_rom(rom,replacements,output_path,exec_changes)
    built=output_path.read_bytes();newfiles=rom_files(built)
    assert newfiles.keys()==files.keys()
    for key,body in replacements.items():assert newfiles[key]==body,key
    for key,body in files.items():
        if key not in replacements:assert newfiles[key]==body,key
    after=decomp_exec(built)
    for key,body in exec_changes.items():assert after[key]==body,key
    for key,body in decomp_exec(rom).items():
        if key not in exec_changes:assert after[key]==body,key
    pages,titles=read_synopsis();verify_synopsis(newfiles['TODS3_OutLineData.dat'],pages,titles)
    assert len(built)==len(rom)
    report=dict(sha256=hashlib.sha256(built).hexdigest(),graphics=graphics,labels=labels,movies=movie_report,
                synopsis=synopsis_report,changed_files=sorted(replacements),
                changed_executables=sorted(exec_changes),runtime_verified=False)
    (report_dir/'ui_localization_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:report[k] for k in ['sha256','changed_files','changed_executables','runtime_verified']},ensure_ascii=False,indent=2))
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--report-dir',type=Path,default=OUT)
    args=parser.parse_args();apply(args.input,args.output,args.report_dir)
