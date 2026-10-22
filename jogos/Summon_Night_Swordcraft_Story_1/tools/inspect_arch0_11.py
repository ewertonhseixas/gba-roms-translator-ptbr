import struct
from pathlib import Path
import sys
sys.path.insert(0, "tools")
from archive_extractor import decompress_gba_lz77

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
base_off = 0x081FCA8C - 0x08000000

# Arch0 [11] is 621168 bytes
off_u, sz_u = struct.unpack_from("<II", rom, base_off + 8 + 11 * 8)
boff = base_off + (off_u << 4)
bsz = sz_u << 4
data11 = rom[boff:boff+bsz]

# Check header of data11
num_entries, ver, w1 = struct.unpack_from("<HHI", data11, 0)
print(f"Arch0 [11]: num_entries={num_entries}, ver={ver}, w1={w1}")

# Check first 5 sub-entries of [11]
for s in range(5):
    soff_u, ssz_u = struct.unpack_from("<II", data11, 8 + s * 8)
    sub = data11[soff_u<<4 : (soff_u<<4) + (ssz_u<<4)]
    is_lz = sub[0] == 0x10 if len(sub) > 0 else False
    if is_lz:
        dec = decompress_gba_lz77(sub)
        if dec: sub = dec[0]
    print(f"  Map {s:03d} in [11]: sz={len(sub)}, is_lz={is_lz}, magic={sub[:8].hex(' ')}")
