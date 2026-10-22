#!/usr/bin/env python3
"""
PSI3 Script VM & Dialogue Inspector
Summon Night: Swordcraft Story (USA) [AB4E]
===========================================
1. Lê as 5 tabelas de opcodes da VM (0x00XX a 0x04XX).
2. Desmonta os handlers de texto/diálogo (ex: 0x0220, 0x0221, etc.).
3. Varre a ROM e os 2.639 scripts descomprimidos em busca de diálogos em inglês
   (tanto ASCII padrão quanto codificação por tabela/16-bit).
"""

import struct
import sys
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from archive_extractor import parse_archive_table, decompress_gba_lz77

GBA_ROM_BASE = 0x08000000

VM_TABLES = [
    (0x0000, 0x081DD5C8, 0x40),
    (0x0100, 0x081F57F8, 0xB0),
    (0x0200, 0x081F5AB8, 0x58),
    (0x0300, 0x081F5C18, 0x30),
    (0x0400, 0x081F5CD8, 0x30),
]


def disasm_func(rom: bytes, func_addr: int, max_insns: int = 45) -> str:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    addr = func_addr & ~1
    off = addr - GBA_ROM_BASE
    chunk = rom[off : off + max_insns * 4]
    out = [f"--- FUNC 0x{addr:08X} ---"]
    for i, insn in enumerate(md.disasm(chunk, addr)):
        if i >= max_insns:
            break
        comment = ""
        if insn.mnemonic == "ldr" and "[pc" in insn.op_str:
            imm = int(insn.op_str.split("#")[1].rstrip("]"), 0)
            pool_addr = ((insn.address + 4) & ~3) + imm
            val = struct.unpack_from("<I", rom, pool_addr - GBA_ROM_BASE)[0]
            comment = f" ; = 0x{val:08X}"
        out.append(f"  0x{insn.address:08X}: {insn.mnemonic:<7} {insn.op_str:<22}{comment}")
        if insn.mnemonic == "bx" and ("lr" in insn.op_str or "r1" in insn.op_str or "r0" in insn.op_str):
            break
    return "\n".join(out)


def main() -> int:
    rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()

    print("=" * 88)
    print(" 1. TABELAS DE OPCODES DA VM DE SCRIPTS (PSI3)")
    print("=" * 88)
    for prefix, tbl_addr, count in VM_TABLES:
        off = tbl_addr - GBA_ROM_BASE
        handlers = []
        for i in range(count):
            ptr = struct.unpack_from("<I", rom, off + i * 4)[0]
            if 0x08000000 <= ptr < 0x08800000:
                handlers.append((prefix | i, ptr))
            elif ptr != 0:
                break
        print(f" Tabela 0x{prefix:04X} @ 0x{tbl_addr:08X}: {len(handlers)} opcodes válidos")
        for op, ptr in handlers[:12]:
            print(f"   Opcode 0x{op:04X} -> 0x{ptr & ~1:08X}")
        if len(handlers) > 12:
            print(f"   ... (+{len(handlers)-12} opcodes)")

    # Mostra especificamente os opcodes 0x0210..0x0235
    print("\n" + "=" * 88)
    print(" 2. OPCODES 0x0200..0x023F (DIÁLOGO / CENÁRIO / MENU)")
    print("=" * 88)
    tbl02_off = 0x081F5AB8 - GBA_ROM_BASE
    for i in range(0x40):
        ptr = struct.unpack_from("<I", rom, tbl02_off + i * 4)[0]
        if ptr:
            print(f"  Opcode 0x02{i:02X} -> 0x{ptr & ~1:08X}")

    # Desmonta 0x0800CEF4 (leitor de argumentos da VM) e os handlers de 0x0220, 0x0221, 0x0222, 0x0223
    print("\n" + "=" * 88)
    print(" 3. DISASSEMBLY DE 0x0800CEF4 E HANDLERS 0x0220..0x0225")
    print("=" * 88)
    print(disasm_func(rom, 0x0800CEF4, 30))
    for op_low in (0x20, 0x21, 0x22, 0x23, 0x24, 0x25):
        ptr = struct.unpack_from("<I", rom, tbl02_off + op_low * 4)[0]
        if ptr:
            print(f"\n[Handler Opcode 0x02{op_low:02X}]")
            print(disasm_func(rom, ptr, 45))

    return 0


if __name__ == "__main__":
    sys.exit(main())
