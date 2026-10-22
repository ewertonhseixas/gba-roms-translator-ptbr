#!/usr/bin/env python3
"""
Text Engine & English Dialogue Locator
Summon Night: Swordcraft Story (USA) [AB4E]
===========================================
1. Encontra todas as funções no código (0x080000C0..0x0806FFFF) que acessam:
   - 0x030043A0 .. 0x03004590 (Buffers de ponteiros de strings dos Opcodes 0x0218, 0x0220, 0x0221)
   - Archive #3 Index 0 (0x087077EC - Bitmap Font "BIT\0")
2. Procura texto em inglês na ROM (tanto ASCII direto quanto codificado por tabela/offset)
   e dentro dos 2.639 scripts PSI3 descomprimidos.
"""

import struct
import sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from archive_extractor import parse_archive_table, decompress_gba_lz77

GBA_ROM_BASE = 0x08000000


def find_literal_refs(rom: bytes, start_val: int, end_val: int) -> list:
    refs = []
    for off in range(0xC0, 0x70000, 4):
        val = struct.unpack_from("<I", rom, off)[0]
        if start_val <= val <= end_val:
            refs.append((GBA_ROM_BASE + off, val))
    return refs


def disasm_range(rom: bytes, start_addr: int, size: int) -> str:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    off = start_addr - GBA_ROM_BASE
    lines = []
    for insn in md.disasm(rom[off : off + size], start_addr):
        c = ""
        if insn.mnemonic == "ldr" and "[pc" in insn.op_str:
            imm = int(insn.op_str.split("#")[1].rstrip("]"), 0)
            pool_addr = ((insn.address + 4) & ~3) + imm
            if 0 <= pool_addr - GBA_ROM_BASE <= len(rom) - 4:
                val = struct.unpack_from("<I", rom, pool_addr - GBA_ROM_BASE)[0]
                c = f" ; = 0x{val:08X}"
        lines.append(f"  0x{insn.address:08X}: {insn.mnemonic:<7} {insn.op_str:<24}{c}")
    return "\n".join(lines)


def search_english_across_rom_and_psi3(rom: bytes) -> None:
    """
    Procura palavras conhecidas de Summon Night: Swordcraft Story (ex: 'Craftknight', 'Cleru',
    'Pratty', 'Wistario', 'Guardian', 'Beast', 'Sword', 'Bron', 'Shintetsu', 'Sanary', 'Razzy', 'Sugar')
    em:
    1) ROM bruta (ASCII e UTF-16LE e Relative Search / César)
    2) Todos os sub-arquivos descomprimidos dos Archives 0, 1, 2, 3
    """
    keywords = [b"Craftknight", b"Wistario", b"Guardian", b"Pratty", b"Cleru", b"Shintetsu", b"Sword", b"Bron"]
    print("=" * 88)
    print(" BUSCA DE PALAVRAS-CHAVE EM INGLÊS NA ROM BRUTA")
    print("=" * 88)
    for kw in keywords:
        pos = 0
        hits = []
        while True:
            idx = rom.find(kw, pos)
            if idx == -1:
                break
            hits.append(f"0x{GBA_ROM_BASE + idx:08X}")
            pos = idx + 1
        print(f"  • {kw.decode():<14}: {len(hits)} ocorrências -> {hits[:8]}")

    # Busca nos 2639 arquivos PSI3 descomprimidos
    print("\n" + "=" * 88)
    print(" BUSCA DE PALAVRAS-CHAVE NOS 2.639 SCRIPTS PSI3 DESCOMPRIMIDOS (ARCHIVE #2)")
    print("=" * 88)
    arc2 = parse_archive_table(rom, 0x085C10DC, 0x0870771C)
    psi3_hits = []
    total_ascii_scripts = 0

    for ent in arc2:
        res = decompress_gba_lz77(rom, ent["file_offset"])
        if not res:
            continue
        decomp, _ = res
        # Verifica se há qualquer uma das keywords
        for kw in keywords:
            idx = decomp.find(kw)
            if idx != -1:
                snippet = decomp[max(0, idx - 16) : min(len(decomp), idx + 64)]
                psi3_hits.append((ent["index"], ent["rom_addr"], kw.decode(), idx, snippet))
                break
        if b"the " in decomp or b"you " in decomp:
            total_ascii_scripts += 1

    print(f"  [+] Total de scripts PSI3 contendo 'the ' ou 'you ' em ASCII puro: {total_ascii_scripts}")
    for f_idx, r_addr, kw_s, off_in_s, snip in psi3_hits[:15]:
        clean = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in snip)
        print(f"  • Script #{f_idx:04d} ({r_addr}) @ +0x{off_in_s:04X} [{kw_s}]: {clean}")


def main() -> int:
    rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()

    refs = find_literal_refs(rom, 0x030043A0, 0x03004590)
    print("=" * 88)
    print(f" XREFS PARA O CONTEXTO DE TEXTO/DIÁLOGO (0x030043A0..0x03004590): {len(refs)} pools")
    print("=" * 88)
    for pool_addr, target in refs:
        print(f"  Pool @ 0x{pool_addr:08X} -> 0x{target:08X}")

    search_english_across_rom_and_psi3(rom)
    return 0


if __name__ == "__main__":
    sys.exit(main())
