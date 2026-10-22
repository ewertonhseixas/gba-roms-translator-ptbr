import struct
from pathlib import Path
import sys
sys.path.insert(0, "tools")
from archive_extractor import decompress_gba_lz77

rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
base_off = 0x081FCA8C - 0x08000000

off_u, sz_u = struct.unpack_from("<II", rom, base_off + 8 + 13 * 8)
boff = base_off + (off_u << 4)
data = rom[boff:boff+(sz_u<<4)]

soff_u, ssz_u = struct.unpack_from("<II", data, 8 + 0 * 8)
hap = data[soff_u<<4 : (soff_u<<4) + (ssz_u<<4)]
if hap[0] == 0x10:
    hap = decompress_gba_lz77(hap)[0]

print("HAP header (first 32 bytes):")
for i in range(0, 32, 4):
    w = struct.unpack_from("<I", hap, i)[0]
    print(f"  [0x{i:02X}]: 0x{w:08X} ({w})")
