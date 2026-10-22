import struct
from pathlib import Path
import sys
sys.path.insert(0, "tools")
from archive_extractor import decompress_gba_lz77

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
base_off = 0x0870771C - 0x08000000
off_u, sz_u = struct.unpack_from("<II", rom, base_off + 8 + 15 * 8)
boff = base_off + (off_u << 4)
data = rom[boff:boff+(sz_u<<4)]

def get_sub(s):
    soff_u, ssz_u = struct.unpack_from("<II", data, 8 + s * 8)
    sub = data[soff_u<<4 : (soff_u<<4) + (ssz_u<<4)]
    return decompress_gba_lz77(sub)[0]

sub18 = get_sub(18)
sub19 = get_sub(19)

print("Sub 18 (CG4) header:")
for i in range(0, 0x30, 4):
    print(f"  [0x{i:02X}]: 0x{struct.unpack_from('<I', sub18, i)[0]:08X}")

print("\nSub 19 (ANP) dump:")
for i in range(0, min(len(sub19), 64), 4):
    print(f"  [0x{i:02X}]: 0x{struct.unpack_from('<I', sub19, i)[0]:08X}")
