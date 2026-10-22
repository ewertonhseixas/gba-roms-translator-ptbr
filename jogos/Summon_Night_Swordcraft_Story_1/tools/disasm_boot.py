#!/usr/bin/env python3
"""
GBA ARM7TDMI / THUMB Disassembler & Boot Analyzer
Summon Night: Swordcraft Story (USA) [AB4E]
==================================================
Desmonta o Entry Point (0x08000000 -> 0x080000C0), a rotina crt0 (ARM),
a rotina de interrupção (IntrMain) e o início do AgbMain (THUMB),
resolvendo Literal Pools ([pc, #imm]), nomes de registradores de I/O do GBA
e chamadas SWI da BIOS.
"""

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

try:
    from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM, CS_MODE_THUMB
    HAS_CAPSTONE = True
except ImportError:
    HAS_CAPSTONE = False

GBA_ROM_BASE = 0x08000000

# Mapeamento de Registradores de Hardware do GBA (I/O + Vetores de BIOS/RAM)
GBA_HW_SYMBOLS: Dict[int, str] = {
    0x03007FFA: "REG_IME_MIRROR_CHECK",
    0x03007FF8: "REG_INTR_CHECK_BUF",
    0x03007FFC: "REG_ISR_VECTOR",
    0x04000000: "REG_DISPCNT",
    0x04000004: "REG_DISPSTAT",
    0x04000006: "REG_VCOUNT",
    0x04000008: "REG_BG0CNT",
    0x0400000A: "REG_BG1CNT",
    0x0400000C: "REG_BG2CNT",
    0x0400000E: "REG_BG3CNT",
    0x040000B0: "REG_DMA0SAD",
    0x040000B4: "REG_DMA0DAD",
    0x040000B8: "REG_DMA0CNT",
    0x040000BC: "REG_DMA1SAD",
    0x040000C0: "REG_DMA1DAD",
    0x040000C4: "REG_DMA1CNT",
    0x040000C8: "REG_DMA2SAD",
    0x040000CC: "REG_DMA2DAD",
    0x040000D0: "REG_DMA2CNT",
    0x040000D4: "REG_DMA3SAD",
    0x040000D8: "REG_DMA3DAD",
    0x040000DC: "REG_DMA3CNT",
    0x04000130: "REG_KEYINPUT",
    0x04000200: "REG_IE",
    0x04000202: "REG_IF",
    0x04000204: "REG_WAITCNT",
    0x04000208: "REG_IME",
}

GBA_BIOS_SWI: Dict[int, str] = {
    0x00: "SoftReset",
    0x01: "RegisterRamReset",
    0x02: "Halt",
    0x03: "Stop",
    0x04: "IntrWait",
    0x05: "VBlankIntrWait",
    0x06: "Div",
    0x07: "DivArm",
    0x08: "Sqrt",
    0x09: "ArcTan",
    0x0A: "ArcTan2",
    0x0B: "CpuSet",
    0x0C: "CpuFastSet",
    0x0E: "BgAffineSet",
    0x0F: "ObjAffineSet",
    0x11: "LZ77UnCompWram",
    0x12: "LZ77UnCompVram",
    0x13: "HuffUnComp",
    0x14: "RLUnCompWram",
    0x15: "RLUnCompVram",
}


def resolve_pc_relative_ldr(rom: bytes, insn_addr: int, op_str: str, is_thumb: bool) -> Optional[Tuple[int, int]]:
    """
    Se a instrução for `ldr rX, [pc, #imm]`, calcula o endereço da literal pool
    na ROM e retorna (pool_addr, word_value).
    """
    if "[pc" not in op_str:
        return None
    # Extrai o imediato após #
    imm = 0
    if "#" in op_str:
        try:
            imm_part = op_str.split("#")[1].rstrip("]").strip()
            imm = int(imm_part, 0)
        except ValueError:
            return None

    if is_thumb:
        # Em THUMB, PC para LDR é ((insn_addr + 4) & ~3) + imm
        pool_addr = ((insn_addr + 4) & ~3) + imm
    else:
        # Em ARM, PC é insn_addr + 8 + imm
        pool_addr = insn_addr + 8 + imm

    file_off = pool_addr - GBA_ROM_BASE
    if 0 <= file_off <= len(rom) - 4:
        val = struct.unpack_from("<I", rom, file_off)[0]
        return (pool_addr, val)
    return None


def annotate_value(val: int) -> str:
    """Retorna uma anotação legível para um valor de 32 bits carregado na CPU."""
    if val in GBA_HW_SYMBOLS:
        return f"{GBA_HW_SYMBOLS[val]} (0x{val:08X})"
    if 0x08000000 <= val < 0x0A000000:
        if val & 1:
            return f"ROM_THUMB_FUNC(0x{val & ~1:08X})"
        return f"ROM_PTR(0x{val:08X})"
    if 0x02000000 <= val < 0x02040000:
        return f"EWRAM(0x{val:08X})"
    if 0x03000000 <= val < 0x03008000:
        return f"IWRAM(0x{val:08X})"
    if 0x04000000 <= val < 0x04000400:
        return f"IOREG(0x{val:08X})"
    if 0x05000000 <= val < 0x05000400:
        return f"PLTT(0x{val:08X})"
    if 0x06000000 <= val < 0x06018000:
        return f"VRAM(0x{val:08X})"
    if 0x07000000 <= val < 0x07000400:
        return f"OAM(0x{val:08X})"
    return f"0x{val:08X}"


def disassemble_region(
    rom: bytes, start_rom_addr: int, size_bytes: int, is_thumb: bool = False
) -> List[Dict[str, Any]]:
    if not HAS_CAPSTONE:
        raise RuntimeError("A biblioteca 'capstone' não está instalada. Execute: pip install capstone")

    mode = CS_MODE_THUMB if is_thumb else CS_MODE_ARM
    md = Cs(CS_ARCH_ARM, mode)
    file_off = start_rom_addr - GBA_ROM_BASE
    code = rom[file_off : file_off + size_bytes]

    lines = []
    # Rastreia endereços de literal pool descobertos para anotá-los como .word
    literal_pools: Dict[int, int] = {}

    for insn in md.disasm(code, start_rom_addr):
        comment = ""
        # Verifica se a instrução lê de uma literal pool [pc, #imm]
        if insn.mnemonic.startswith("ldr"):
            res = resolve_pc_relative_ldr(rom, insn.address, insn.op_str, is_thumb)
            if res:
                pool_addr, val = res
                literal_pools[pool_addr] = val
                comment = f"; = {annotate_value(val)} [pool @ 0x{pool_addr:08X}]"

        # Verifica chamadas SWI da BIOS
        if insn.mnemonic in ("swi", "svc"):
            try:
                swi_num = int(insn.op_str.lstrip("#"), 0)
                if not is_thumb:
                    swi_num >>= 16
                swi_name = GBA_BIOS_SWI.get(swi_num, f"SWI_0x{swi_num:02X}")
                comment = f"; BIOS::{swi_name}()"
            except ValueError:
                pass

        raw_hex = " ".join(f"{b:02X}" for b in insn.bytes)
        lines.append({
            "address": f"0x{insn.address:08X}",
            "bytes": raw_hex,
            "mnemonic": insn.mnemonic,
            "op_str": insn.op_str,
            "comment": comment,
        })

    return lines


def print_disasm_block(title: str, lines: List[Dict[str, Any]]) -> None:
    print("=" * 88)
    print(f" {title}")
    print("=" * 88)
    for ln in lines:
        c = f"  {ln['comment']}" if ln["comment"] else ""
        print(f" {ln['address']}:  {ln['bytes']:<12}  {ln['mnemonic']:<8} {ln['op_str']:<26}{c}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Desmonta o boot e AgbMain de Summon Night: Swordcraft Story")
    parser.add_argument(
        "rom",
        nargs="?",
        default="rom/Summon Night - Swordcraft Story (USA).gba",
        help="Caminho para a ROM .gba",
    )
    parser.add_argument("--addr", type=lambda x: int(x, 0), default=0x080000C0, help="Endereço ROM inicial")
    parser.add_argument("--size", type=lambda x: int(x, 0), default=0x280, help="Bytes para desmontar")
    parser.add_argument("--thumb", action="store_true", help="Desmontar em modo THUMB (16-bit)")
    args = parser.parse_args()

    rom_path = Path(args.rom)
    if not rom_path.exists():
        print(f"[!] ROM não encontrada em: {rom_path}", file=sys.stderr)
        return 1

    rom = rom_path.read_bytes()
    lines = disassemble_region(rom, args.addr, args.size, is_thumb=args.thumb)
    mode_str = "THUMB (16-bit)" if args.thumb else "ARM (32-bit)"
    print_disasm_block(f"DISASSEMBLY [{mode_str}] @ 0x{args.addr:08X} ({args.size} bytes)", lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
