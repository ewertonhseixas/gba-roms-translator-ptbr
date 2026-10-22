import struct
from pathlib import Path

sav = Path("rom/Summon Night - Swordcraft Story (USA).sav").read_bytes()
print(f"Save file size: {len(sav)} bytes")

# Check non-zero blocks
non_zero_chunks = []
for i in range(0, len(sav), 64):
    chunk = sav[i:i+64]
    if any(b != 0xFF and b != 0x00 for b in chunk):
        non_zero_chunks.append((i, chunk))

print(f"Non-empty 64-byte chunks: {len(non_zero_chunks)}")
for off, chunk in non_zero_chunks[:10]:
    ascii_c = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk[:32])
    print(f"  [0x{off:04X}]: {chunk[:16].hex(' ')} | {ascii_c}")
