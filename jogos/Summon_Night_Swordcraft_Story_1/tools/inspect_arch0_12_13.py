import struct
from pathlib import Path
import sys
sys.path.insert(0, "tools")
from archive_extractor import decompress_gba_lz77

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
base_off = 0x081FCA8C - 0x08000000

def check_file(f_idx):
    off_u, sz_u = struct.unpack_from("<II", rom, base_off + 8 + f_idx * 8)
    boff = base_off + (off_u << 4)
    data = rom[boff:boff+(sz_u<<4)]
    num_entries, ver, w1 = struct.unpack_from("<HHI", data, 0)
    print(f"Arch0 [{f_idx}]: num_entries={num_entries}")
    for s in range(3):
        soff_u, ssz_u = struct.unpack_from("<II", data, 8 + s * 8)
        sub = data[soff_u<<4 : (soff_u<<4) + (ssz_u<<4)]
        if len(sub) > 0 and sub[0] == 0x10:
            dec = decompress_gba_lz77(sub)
            if dec: sub = dec[0]
        print(f"  [{f_idx}][{s}]: sz={len(sub)}, magic={sub[:8].hex(' ')} | {sub[:4]}")

check_file(12)
check_file(13)
