"""Indexed Nitro graphics inspection and localization, without image dependencies."""
from pathlib import Path
import struct
import zlib
from math import ceil

from toh_full_audit import rom_files, fps4, unpack
from verify_accent_fonts import Font
from nftr_ptbr_injector import _get_pixel
from toh_text_builder_v2 import CHAR_CODES

BASE = Path(__file__).resolve().parents[1]
OUT = BASE/'build/ui_localization_2026-11-18'
SIZES = {(0,0):(8,8),(0,1):(16,16),(0,2):(32,32),(0,3):(64,64),
         (1,0):(16,8),(1,1):(32,8),(1,2):(32,16),(1,3):(64,32),
         (2,0):(8,16),(2,1):(8,32),(2,2):(16,32),(2,3):(32,64)}


def palette(data):
    at = data.index(b'TTLP')
    size, off = struct.unpack_from('<II',data,at+16)
    raw = data[at+8+off:at+8+off+size]
    return [((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31)
            for v in struct.unpack('<'+'H'*(len(raw)//2),raw)]


def tiles(data):
    at=data.index(b'RAHC');size,off=struct.unpack_from('<II',data,at+24)
    depth=8 if struct.unpack_from('<I',data,at+12)[0]==4 else 4
    start=at+8+off;raw=data[start:start+size]
    flat=list(raw) if depth==8 else [p for b in raw for p in (b&15,b>>4)]
    return depth,start,size,[flat[i:i+64] for i in range(0,len(flat),64)]


def png(path, pixels, width, height, colors):
    def chunk(kind,body):
        return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body))
    pal=list(colors)+[(0,0,0)]*(256-len(colors))
    raw=b''.join(b'\0'+bytes(pixels[y*width:(y+1)*width]) for y in range(height))
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,3,0,0,0))
                     +chunk(b'PLTE',bytes(c for rgb in pal[:256] for c in rgb))
                     +chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))


def text(pixels,width,height,value,x,y,font,ink):
    for char in value:
        raw=char.encode('cp932') if char not in CHAR_CODES else None
        cp=CHAR_CODES[char] if raw is None else int.from_bytes(raw,'big')
        cell,(left,_,advance)=font.cell_for(cp)
        for yy in range(font.height):
            for xx in range(font.width):
                if _get_pixel(cell,font.width,font.bpp,xx,yy):
                    dx,dy=x+left+xx,y+yy
                    if 0<=dx<width and 0<=dy<height:pixels[dy*width+dx]=ink
        x+=advance
    return x


def atlas(data, columns=32):
    _,_,_,ts=tiles(data);w=columns*8;h=ceil(len(ts)/columns)*8
    im=[0]*(w*h)
    for i,tile in enumerate(ts):
        for y in range(8):
            for x in range(8):im[((i//columns)*8+y)*w+(i%columns)*8+x]=tile[y*8+x]
    return im,w,h


def cell_layout(data):
    at=data.index(b'KBEC');count,kind,off=struct.unpack_from('<HHI',data,at+8)
    shift=struct.unpack_from('<I',data,at+16)[0]&3;stride=16 if kind==1 else 8
    base=at+8+off;oam=base+count*stride;cells=[]
    for i in range(count):
        n,_,rel=struct.unpack_from('<HHI',data,base+i*stride);parts=[]
        for j in range(n):
            a,b,c=struct.unpack_from('<HHH',data,oam+rel+j*6)
            x,y=b&511,a&255;x=x-512 if x>=256 else x;y=y-256 if y>=128 else y
            w,h=SIZES.get((a>>14,b>>14),(8,8))
            parts.append(dict(x=x,y=y,w=w,h=h,tile=(c&1023)<<shift,bank=c>>12,
                              flipx=bool(b&4096),flipy=bool(b&8192)))
        cells.append(parts)
    return cells


def render_cell(gfx,parts):
    depth,_,_,ts=tiles(gfx)
    x0=min(p['x'] for p in parts);y0=min(p['y'] for p in parts)
    w=max(p['x']+p['w'] for p in parts)-x0;h=max(p['y']+p['h'] for p in parts)-y0
    im=[0]*(w*h);addresses={}
    for p in reversed(parts):
        for y in range(p['h']):
            for x in range(p['w']):
                tile=p['tile']//(2 if depth==8 else 1)+(y//8)*(p['w']//8)+x//8
                if tile>=len(ts):continue
                val=ts[tile][(y%8)*8+x%8]
                xx=p['x']-x0+(p['w']-1-x if p['flipx'] else x)
                yy=p['y']-y0+(p['h']-1-y if p['flipy'] else y)
                pos=yy*w+xx
                addresses[pos]=tile*64+(y%8)*8+x%8
                if val:im[pos]=val+(p['bank']*16 if depth==4 else 0)
    return im,w,h,addresses


def inspect():
    OUT.mkdir(exist_ok=True)
    files=rom_files((BASE/'build/Tales of Hearts - Anime Movie Edition (PT-BR).nds').read_bytes())
    font=Font(files['trialFont10.NFTR'])
    title={n:unpack(d)[0] for n,_,_,_,d in fps4(files['title/t.dat'],files['title/t.dat'])}
    for prefix,pack,g,c,p in [('title',title,'TITLE_OBJ.NCGR_LZ','TITLE_OBJ.NCER_LZ','TITLE_OBJ.NCLR_LZ')]:
        colors=palette(pack[p]);im,w,h=atlas(pack[g]);png(OUT/(prefix+'_atlas.png'),im,w,h,colors)
        cells=cell_layout(pack[c]);sheet=[0]*(512*(ceil(len(cells)/4)*88))
        for i,parts in enumerate(cells):
            if not parts:continue
            im,w,h,_=render_cell(pack[g],parts);png(OUT/f'{prefix}_cell_{i:02}.png',im,w,h,colors)
            ox=(i%4)*128;oy=(i//4)*88
            text(sheet,512,len(sheet)//512,str(i),ox,oy,font,min(1,len(colors)-1))
            for yy in range(min(h,68)):
                for xx in range(min(w,128)):sheet[(oy+16+yy)*512+ox+xx]=im[yy*w+xx]
        png(OUT/(prefix+'_cells.png'),sheet,512,len(sheet)//512,colors)
    menu={n:unpack(d)[0] for n,_,_,_,d in fps4(files['menu/MENU_BG.b'],files['menu/MENU_BG.dat'])}
    names=sorted(n[:-3] for n in menu if n.endswith('_OBJ.CC') and n[:-3]+'.PP' in menu)
    for start in range(0,len(names),8):
        # Use RGB output palette quantization per panel via a common grayscale preview.
        sheet=[0]*(512*256);gray=[(i,i,i) for i in range(256)]
        for j,key in enumerate(names[start:start+8]):
            im,w,h=atlas(menu[key+'.CC'],16);pal=palette(menu[key+'.PP'])
            ox=(j%4)*128;oy=(j//4)*128
            text(sheet,512,256,key.replace('MENU_',''),ox,oy,font,255)
            for y in range(min(h,112)):
                for x in range(min(w,128)):
                    v=im[y*w+x];rgb=pal[v] if v<len(pal) else (255,255,255)
                    sheet[(oy+16+y)*512+ox+x]=max(rgb) if v else 25
        png(OUT/f'menu_atlases_{start//8}.png',sheet,512,256,gray)
    print('Generated title and',len(names),'menu sprite atlas previews:',OUT)


def pack_tiles(data, flat):
    depth,start,size,_=tiles(data)
    raw=bytes(flat) if depth==8 else bytes(flat[i]|flat[i+1]<<4 for i in range(0,len(flat),2))
    assert len(raw)==size
    return data[:start]+raw+data[start+size:]


def lz11_literal(data):
    result=bytearray(b'\x11'+len(data).to_bytes(3,'little'))
    for i in range(0,len(data),8): result.extend(b'\0'+data[i:i+8])
    assert unpack(bytes(result))[0]==data
    return bytes(result)


def rebuild_self_archive(data, replacements):
    entries=list(fps4(data,data));first=min(e[1] for e in entries)
    result=bytearray(data[:first]);count,head=struct.unpack_from('<II',data,4)
    stride=struct.unpack_from('<H',data,16)[0]
    for i in range(count):
        at=head+i*stride;old,stored,size=struct.unpack_from('<III',data,at)
        if old==0xffffffff or not stored:continue
        name=data[at+12:at+stride].split(b'\0')[0].decode('ascii')
        body=replacements.get(name,data[old:old+stored])
        result.extend(b'\0'*(-len(result)%16));off=len(result)
        result.extend(body);result.extend(b'\0'*(-len(result)%16))
        decoded=body if name in replacements else None
        struct.pack_into('<III',result,at,off,len(result)-off,len(decoded) if decoded is not None else size)
    assert len(list(fps4(result,result)))==len(entries)
    return bytes(result)



def rebuild_menu_archive(index,payload,replacements):
    result=bytearray();idx=bytearray(index)
    count,head=struct.unpack_from('<II',index,4)
    stride,mask=struct.unpack_from('<HH',index,16)
    assert mask==11,mask
    for i in range(count):
        at=head+i*stride
        old,size=struct.unpack_from('<II',index,at)
        if old==0xffffffff or not size:continue
        name=index[at+8:at+stride].split(b'\0')[0].decode('ascii')
        body=replacements.get(name,payload[old:old+size])
        result.extend(b'\0'*(-len(result)%4));off=len(result)
        result.extend(body)
        struct.pack_into('<II',idx,at,off,len(body))
    assert len(list(fps4(idx,result)))==len(list(fps4(index,payload)))
    return bytes(idx),bytes(result)


def localize_poem(data,screen,colors,font,lines):
    depth,_,_,ts=tiles(data);assert depth==8
    flat=[x for tile in ts for x in tile]
    at=screen.index(b'NRCS');width,height=struct.unpack_from('<HH',screen,at+8)
    assert (width,height)==(256,256)
    image=[0]*(width*height);addresses={}
    for i,v in enumerate(struct.unpack_from('<1024H',screen,at+20)):
        for y in range(8):
            for x in range(8):
                tx,ty=(7-x if v&1024 else x),(7-y if v&2048 else y)
                pos=((i//32)*8+y)*width+(i%32)*8+x
                address=(v&1023)*64+ty*8+tx
                image[pos]=flat[address];addresses[pos]=address
    before=list(image);cache={}
    def nearest(rgb):
        key=tuple(rgb)
        if key not in cache:cache[key]=min(range(len(colors)),key=lambda i:sum((colors[i][j]-rgb[j])**2 for j in range(3)))
        return cache[key]
    for stanza in range(5):
        top=26+24*stanza;bottom=42+24*stanza+(2 if stanza==4 else 0)
        for x in range(17,136):
            a=colors[before[(top-1)*width+x]];b=colors[before[bottom*width+x]]
            for y in range(top,bottom):
                fraction=(y-top+1)/(bottom-top+1)
                rgb=tuple(round(a[k]*(1-fraction)+b[k]*fraction) for k in range(3))
                image[y*width+x]=nearest(rgb)
    # A parchment inset keeps the small poem legible over both moving title palettes.
    for y in range(21,146):
        for x in range(12,142):
            if (x<15 or x>138) and (y<24 or y>142):continue
            old=colors[image[y*width+x]]
            edge=x in (12,141) or y in (21,145)
            paper=(143,112,78) if edge else (235,220,190)
            alpha=0.65 if edge else 0.94
            image[y*width+x]=nearest(tuple(round(old[k]*(1-alpha)+paper[k]*alpha) for k in range(3)))
    ink=nearest((130,63,43))
    for i,line in enumerate(lines):
        assert text([0]*2048,256,8,line,0,0,font,ink)<=118,line
        text(image,width,height,line,18,26+(i//2)*24+(i%2)*10,font,ink)
    for pos,value in enumerate(image):
        if value!=before[pos]:flat[addresses[pos]]=value
    assert all(flat[addresses[pos]]==value for pos,value in enumerate(image)), 'Shared background tile changed another pixel'
    return pack_tiles(data,flat),image

def localize_graphics(files, preview_dir=OUT):
    """Change pixel indices only; retain palettes, OAM geometry and texture dimensions."""
    preview_dir.mkdir(parents=True,exist_ok=True)
    font=Font(files['trialFont10.NFTR']);small=Font(files['trialFont8.NFTR'])
    original=files['title/t.dat'];pack={n:unpack(d)[0] for n,_,_,_,d in fps4(original,original)}
    source_files=rom_files((BASE/'rom/Tales of Hearts - Anime Movie Edition (EN).nds').read_bytes())
    source={n:unpack(d)[0] for n,_,_,_,d in fps4(source_files['title/t.dat'],source_files['title/t.dat'])}
    replacements={};report=[]
    for key,value in [('NEWGAME','Novo Jogo'),('LOADGAME','Carregar'),('CUSTOM','Opções'),('MUSEUM','Galeria')]:
        for state in (1,2):
            name=f'{key}_{state}.DS3'
            # CUSTOM uses two textures (32px + 8px). A single 64px model avoids
            # leaving the original second texture visible beneath the new label.
            data=source[f'NEWGAME_{state}.DS3'] if key=='CUSTOM' else source[name]
            width=64;height=16;ink=1 if state==1 else 15
            start=struct.unpack_from('<I',data,24)[0];size=width*height//2
            canvas=[0]*(width*height);advance=text(canvas,width,height,value,0,0,font,ink)
            assert advance<=width,(name,advance,width)
            canvas=[0]*(width*height);text(canvas,width,height,value,(width-advance)//2,2,font,ink)
            raw=bytes(canvas[i]|canvas[i+1]<<4 for i in range(0,len(canvas),2))
            updated=data[:start]+raw+data[start+size:];assert len(updated)==len(data)
            replacements[name]=updated
            paloff=struct.unpack_from('<I',data,8)[0]
            pal=[((v&31)*255//31,((v>>5)&31)*255//31,((v>>10)&31)*255//31) for v in struct.unpack_from('<16H',data,paloff)]
            png(preview_dir/(name+'.png'),canvas,width,height,pal)
            report.append(dict(resource='title/t.dat/'+name,text=value))
    name='TITLE_OBJ.NCGR_LZ';data=source[name];parts=cell_layout(source['TITLE_OBJ.NCER_LZ'])[4][2:]
    canvas,w,h,addresses=render_cell(data,parts);flat=[x for tile in tiles(data)[3] for x in tile]
    # Clear only the three text OAM parts. Diamond sprites overlap their bounding
    # box and share their tiles, so clearing a rectangular composite damages both.
    for address in addresses.values():flat[address]=0
    localized=[0]*(w*h);label='APERTE START'
    advance=text([0]*(w*h),w,h,label,0,0,font,15)
    assert advance<=80
    text(localized,w,h,label,(w-advance)//2,1,font,15)
    # A centered one-pixel contour follows the glyph mask, without drawing
    # another offset copy of the text (which previously looked duplicated).
    foreground=tuple(localized)
    for pos,value in enumerate(foreground):
        if not value:continue
        x,y=pos%w,pos//w
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                xx,yy=x+dx,y+dy
                if 0<=xx<w and 0<=yy<h and not foreground[yy*w+xx]:
                    localized[yy*w+xx]=1
    for pos,value in enumerate(localized):
        if value and pos in addresses:flat[addresses[pos]]=value
    updated=pack_tiles(data,flat);replacements[name]=lz11_literal(updated)
    im,w,h,_=render_cell(updated,parts);png(preview_dir/'pressione_start.png',im,w,h,palette(pack['TITLE_OBJ.NCLR_LZ']))
    assert im==[value+48 if value else 0 for value in localized], 'Prompt differs from outlined glyph mask'
    report.append(dict(resource='title/t.dat/'+name,text=label))

    poem=[]
    for line in (BASE/'ARQUIVOS md/interface-grafica.md').read_text(encoding='utf8').splitlines():
        cells=line.split('|')
        if len(cells)>4 and cells[1].strip().startswith('POEMA'):poem.extend(cells[3].strip().split('<br>'))
    assert len(poem)==10
    for name,palname in [('TITLE_2_1.NCGR_LZ','TITLE.NCLR_LZ'),('TITLE_2_2.NCGR_LZ','TITLE2.NCLR_LZ')]:
        colors=palette(source[palname])[256:]
        screen=source[name.replace('NCGR','NSCR')]
        localized,preview=localize_poem(source[name],screen,colors,font,poem)
        replacements[name]=lz11_literal(localized)
        png(preview_dir/(name+'.png'),preview,256,256,colors)
        report.append(dict(resource='title/t.dat/'+name,text='Poema da Princesa dos Espinhos'))
    result={'title/t.dat':rebuild_self_archive(original,replacements)}

    # The green New tab is drawn into the item screen's background tiles.
    menu={n:unpack(d)[0] for n,_,_,_,d in fps4(files['menu/MENU_BG.b'],files['menu/MENU_BG.dat'])}
    data=menu['MENU_ITEM.CC'];flat=[x for tile in tiles(data)[3] for x in tile]
    scr=menu['MENU_ITEM.SS'];at=scr.index(b'NRCS');canvas=[0]*(19*16)
    assert text(canvas,19,16,'Novo',0,3,small,14)<=19
    changed=set()
    for y in range(16):
        for x in range(19):
            xx,yy=115+x,4+y
            v=struct.unpack_from('<H',scr,at+20+((yy//8)*32+xx//8)*2)[0]
            tx,ty=xx%8,yy%8
            if v&1024:tx=7-tx
            if v&2048:ty=7-ty
            pos=(v&1023)*64+ty*8+tx
            flat[pos]=canvas[y*19+x] or 1;changed.add(v&1023)
    idx,body=rebuild_menu_archive(files['menu/MENU_BG.b'],files['menu/MENU_BG.dat'],{'MENU_ITEM.CC':lz11_literal(pack_tiles(data,flat))})
    result.update({'menu/MENU_BG.b':idx,'menu/MENU_BG.dat':body})
    report.append(dict(resource='menu/MENU_BG.dat/MENU_ITEM.CC',text='Novo',tiles=sorted(changed)))
    # Lossless decoding and unchanged palette/OAM members are mandatory.
    rebuilt={n:unpack(d)[0] for n,_,_,_,d in fps4(result['title/t.dat'],result['title/t.dat'])}
    for n in pack:
        if n not in replacements:assert rebuilt[n]==pack[n],n
    return result,report


if __name__=='__main__':inspect()
