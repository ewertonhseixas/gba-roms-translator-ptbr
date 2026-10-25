import struct
from pathlib import Path
from build_ptbr_rom import ORIGINAL_ROM, MD_DIR, GBA_ROM_BASE, FREE_SPACE_START, encode_sjis_u16

rom = bytearray(ORIGINAL_ROM.read_bytes())
ui_md = MD_DIR / '00_Interface_Menus_Selecao_e_Sistema.md'

ptr_map = {}
for off in range(0, len(rom) - 4, 4):
    val = struct.unpack_from('<I', rom, off)[0]
    if 0x0808E000 <= val < 0x08095000:
        if val not in ptr_map:
            ptr_map[val] = []
        ptr_map[val].append(off)

lines = ui_md.read_text(encoding='utf-8').splitlines()
relocs = []
for line in lines:
    if not line.startswith('| `0x'):
        continue
    cols = [c.strip() for c in line.strip('|').split('|')]
    if len(cols) >= 3 and cols[2]:
        addr_str = cols[0].strip('` ')
        pt_text = cols[2].strip()
        addr = int(addr_str, 16)
        off = addr - GBA_ROM_BASE
        p = off
        while p + 1 < len(rom) and struct.unpack_from('>H', rom, p)[0] != 0:
            p += 2
        orig_len = (p + 2) - off
        enc = encode_sjis_u16(pt_text)
        if len(enc) > orig_len:
            ptrs = ptr_map.get(addr, [])
            relocs.append((addr_str, pt_text, orig_len, len(enc), ptrs))

print(f'Total relocations: {len(relocs)}')
for addr_str, pt, olen, nlen, ptrs in relocs:
    ptr_hex = [f'0x{0x08000000+p:08X}' for p in ptrs]
    print(f'  {addr_str}: orig {olen}B -> {nlen}B ({pt}) | Pointers found at: {ptr_hex}')
