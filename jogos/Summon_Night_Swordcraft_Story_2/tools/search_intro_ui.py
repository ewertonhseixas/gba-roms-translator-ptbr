import struct
from pathlib import Path
import sys

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
rom = rom_path.read_bytes()

queries = ['NEW GAME', 'New Game', 'CONTINUE', 'Continue', 'Male', 'Female', 'Name', 'Boy', 'Girl', 'Prologue', 'Blaire', 'Colat', 'Orin', 'Edgar']
print("Scanning ROM for ASCII...")
for q in queries:
    pos = 0
    while True:
        idx = rom.find(q.encode('ascii'), pos)
        if idx == -1: break
        print(f"ASCII '{q}' at 0x{idx:06X} (0x{0x08000000+idx:08X})")
        pos = idx + len(q)

print("\nScanning ROM for Full-Width Shift-JIS...")
for q in queries:
    sjis_b = bytearray()
    for c in q:
        if 'A' <= c <= 'Z': sjis_b += struct.pack('>H', 0x8260 + ord(c) - ord('A'))
        elif 'a' <= c <= 'z': sjis_b += struct.pack('>H', 0x8281 + ord(c) - ord('a'))
        elif c == ' ': sjis_b += struct.pack('>H', 0x8140)
    if sjis_b:
        pos = 0
        while True:
            idx = rom.find(bytes(sjis_b), pos)
            if idx == -1: break
            print(f"SJIS '{q}' at 0x{idx:06X} (0x{0x08000000+idx:08X})")
            pos = idx + len(sjis_b)
