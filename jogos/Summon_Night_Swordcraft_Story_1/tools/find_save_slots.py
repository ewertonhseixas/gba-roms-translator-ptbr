from pathlib import Path

sav = Path("rom/Summon Night - Swordcraft Story (PT-BR).sav").read_bytes()
print("Searching for save slot headers...")

for i in range(0, len(sav), 16):
    chunk = sav[i:i+16]
    if b"SCNS" in chunk or b"SNCS" in chunk or b"FILE" in chunk:
        print(f"Header at 0x{i:04X}: {chunk}")
