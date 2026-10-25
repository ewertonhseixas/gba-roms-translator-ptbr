import struct
from pathlib import Path

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
rom = rom_path.read_bytes()

# 1. Search for title screen graphics / strings
# In GBA games, 'NEW GAME' and 'CONTINUE' on the title screen are often:
# a) ASCII string
# b) Shift-JIS string
# c) Tile graphics (CG4 / LZ77)
print("--- Searching for Title Screen text ---")
for word in ['NEW GAME', 'CONTINUE', 'New Game', 'Continue', 'GAME START', 'Game Start']:
    # ASCII
    p = 0
    while True:
        idx = rom.find(word.encode('ascii'), p)
        if idx == -1: break
        print(f"ASCII '{word}' at 0x{idx:06X} (0x{0x08000000+idx:08X})")
        p = idx + len(word)
    # SJIS
    s_bytes = bytearray()
    for c in word:
        if 'A' <= c <= 'Z': s_bytes += struct.pack('>H', 0x8260 + ord(c) - ord('A'))
        elif 'a' <= c <= 'z': s_bytes += struct.pack('>H', 0x8281 + ord(c) - ord('a'))
        elif c == ' ': s_bytes += struct.pack('>H', 0x8140)
    if s_bytes:
        p = 0
        while True:
            idx = rom.find(bytes(s_bytes), p)
            if idx == -1: break
            print(f"SJIS '{word}' at 0x{idx:06X} (0x{0x08000000+idx:08X})")
            p = idx + len(s_bytes)

# 2. Check how SN1 did Title Screen menus
print("\n--- Checking SN1 UI file for title menu ---")
sn1_ui = Path(r"02_TRADUCAO_ROMS_GBA/jogos/Summon_Night_Swordcraft_Story_1/ARQUIVOS md/03-interface-batalha-menus-e-sistema.md")
if sn1_ui.exists():
    for line in sn1_ui.read_text(encoding='utf-8').splitlines():
        if any(w in line for w in ['NEW GAME', 'New Game', 'CONTINUE', 'Continue', 'Male', 'Female']):
            print("  SN1:", line[:100])
