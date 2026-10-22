#!/usr/bin/env python3
"""
GBA Subsystem & Cross-Reference (XREF) Analyzer
Summon Night: Swordcraft Story (USA) [AB4E]
================================================
1. Escaneia o Banco #006 (0x08060000..0x0806FFFF) e toda a ROM em busca de
   strings ASCII/diálogos e tabelas de ponteiros.
2. Encontra todas as referências (Literal Pools em 0x080000C0..0x0805FFFF)
   que apontam para:
   - Banco #006 (0x08060000..0x0806FFFF) ou tabelas de strings
   - VRAM (0x06000000..0x06017FFF)
   - Chamadas SWI de descompressão (LZ77UnCompWram = 0x11, LZ77UnCompVram = 0x12)
3. Constrói o grafo de chamadas (Call Graph) a partir das sub-rotinas de AgbMain
   para identificar exatamente qual sub-rotina gerencia Texto/Diálogo, Scripts e VRAM.
"""

import json
import struct
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any

from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

GBA_ROM_BASE = 0x08000000
CODE_START = 0x080000C0
CODE_END = 0x08060000  # 384 KB de código principal

# Sub-rotinas chamadas diretamente em AgbMain (Init + Main Loop)
AGBMAIN_SUBS: List[Tuple[int, str]] = [
    (0x0800B7E0, "Init+Loop"),
    (0x0800038C, "Init+Loop"),
    (0x0800788C, "Init"),
    (0x08007BB0, "Init"),
    (0x0800E668, "Init"),
    (0x08006F9C, "Init"),
    (0x08001E98, "Init"),
    (0x0800B7DC, "Init"),
    (0x08003900, "Init"),
    (0x0800BEE0, "Init"),
    (0x0800D884, "Init"),
    (0x0800E924, "Init"),
    (0x080071E4, "Init"),
    (0x08008D48, "Init"),
    (0x0800A0F4, "Init"),
    (0x08007CA4, "Init"),
    (0x080329F4, "Init"),
    (0x0803BA60, "Init"),
    (0x0805D3A4, "Init"),
    (0x0800CB78, "Init"),
    (0x08042AAC, "Init"),
    (0x0803ACE4, "Init"),
    (0x080271C8, "Init"),
    (0x0800790C, "Init"),
    (0x0800E4DC, "Init"),
    (0x0800E128, "Init"),
    (0x0800CC28, "Init"),
    (0x0800D230, "Init"),
    (0x0800CC40, "Init"),
    (0x0800CC70, "Init"),
    (0x0800BE44, "Loop"),
    (0x08007898, "Loop"),
    (0x08001E9C, "Loop"),
    (0x08003D8C, "Loop"),
    (0x0800EBC4, "Loop"),
    (0x0800CD18, "Loop"),
    (0x0800E694, "Loop"),
    (0x08007D1C, "Loop"),
    (0x08008EB0, "Loop"),
    (0x0800E154, "Loop"),
    (0x08000398, "Loop"),
    (0x0800B7F4, "Loop"),
    (0x08001EFC, "Loop"),
    (0x08003910, "Loop"),
    (0x0800BEF8, "Loop"),
    (0x08003E8C, "Loop"),
    (0x0800E4C4, "Loop"),
    (0x0806B734, "Loop"),
    (0x0800B954, "Loop"),
    (0x08002034, "Loop"),
    (0x080078C0, "Loop"),
    (0x0800C428, "Loop"),
    (0x08003DA0, "Loop"),
]


def extract_ascii_samples(rom: bytes, start_addr: int, end_addr: int, min_len: int = 5) -> List[Dict[str, Any]]:
    """Extrai strings ASCII legíveis de uma região da ROM para inspeção."""
    start_off = start_addr - GBA_ROM_BASE
    end_off = end_addr - GBA_ROM_BASE
    data = rom[start_off:end_off]
    results = []
    i = 0
    n = len(data)
    while i < n:
        if 0x20 <= data[i] <= 0x7E:
            s_start = i
            chars = []
            while i < n and (0x20 <= data[i] <= 0x7E or data[i] in (0x0A, 0x0D)):
                chars.append(chr(data[i]))
                i += 1
            if len(chars) >= min_len:
                text = "".join(chars).strip()
                if len(text) >= min_len:
                    results.append({
                        "rom_addr": f"0x{start_addr + s_start:08X}",
                        "length": len(text),
                        "sample": text[:64],
                    })
        else:
            i += 1
    return results


def analyze_subroutine_tree(rom: bytes, root_addr: int, max_depth: int = 3, max_func_bytes: int = 0x600) -> Dict[str, Any]:
    """
    Explora recursivamente (BFS até max_depth) uma sub-rotina THUMB chamada por AgbMain,
    coletando:
    - Funções filhas chamadas (BL)
    - Referências de Literal Pool para:
      * VRAM (0x06000000..0x06017FFF)
      * Banco #006 (0x08060000..0x0806FFFF)
      * Outros bancos de dados da ROM (0x08070000..0x087FFFFF)
      * EWRAM (0x02000000..0x0203FFFF)
      * IWRAM (0x03000000..0x03007FFF)
      * Registradores I/O (0x04000000..0x040003FF)
    - Chamadas SWI da BIOS (ex: LZ77UnCompWram, CpuSet, VBlankIntrWait)
    """
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    visited: Set[int] = set()
    queue: deque[Tuple[int, int]] = deque([(root_addr, 0)])

    vram_refs: Set[str] = set()
    bank06_refs: Set[str] = set()
    rom_data_refs: Set[str] = set()
    ewram_refs: Set[str] = set()
    iwram_refs: Set[str] = set()
    ioreg_refs: Set[str] = set()
    swi_calls: Set[str] = set()
    callees: Set[str] = set()

    while queue:
        func_addr, depth = queue.popleft()
        if func_addr in visited or not (GBA_ROM_BASE <= func_addr < GBA_ROM_BASE + len(rom)):
            continue
        visited.add(func_addr)

        file_off = func_addr - GBA_ROM_BASE
        chunk = rom[file_off : file_off + max_func_bytes]

        for insn in md.disasm(chunk, func_addr):
            # 1. Literal Pool load: ldr rX, [pc, #imm]
            if insn.mnemonic == "ldr" and "[pc" in insn.op_str:
                try:
                    imm_part = insn.op_str.split("#")[1].rstrip("]").strip()
                    imm = int(imm_part, 0)
                    pool_addr = ((insn.address + 4) & ~3) + imm
                    pool_off = pool_addr - GBA_ROM_BASE
                    if 0 <= pool_off <= len(rom) - 4:
                        val = struct.unpack_from("<I", rom, pool_off)[0]
                        if 0x06000000 <= val < 0x06018000:
                            vram_refs.add(f"0x{val:08X} (@0x{insn.address:08X})")
                        elif 0x08060000 <= val < 0x08070000:
                            bank06_refs.add(f"0x{val:08X} (@0x{insn.address:08X})")
                        elif 0x08070000 <= val < 0x08800000:
                            rom_data_refs.add(f"0x{val:08X} (@0x{insn.address:08X})")
                        elif 0x02000000 <= val < 0x02040000:
                            ewram_refs.add(f"0x{val:08X}")
                        elif 0x03000000 <= val < 0x03008000:
                            iwram_refs.add(f"0x{val:08X}")
                        elif 0x04000000 <= val < 0x04000400:
                            ioreg_refs.add(f"0x{val:08X}")
                except (ValueError, IndexError):
                    pass

            # 2. Detecção de movimentos imediatos para VRAM (0x06000000 = 0xC0 << 19)
            if insn.mnemonic == "lsls" and "#0x13" in insn.op_str:
                vram_refs.add(f"IMM_0x06000000 (@0x{insn.address:08X})")

            # 3. SWI calls
            if insn.mnemonic in ("svc", "swi"):
                swi_calls.add(f"{insn.op_str} (@0x{insn.address:08X})")

            # 4. Chamadas BL para outras sub-rotinas
            if insn.mnemonic == "bl":
                try:
                    target = int(insn.op_str.lstrip("#"), 0)
                    callees.add(f"0x{target:08X}")
                    if depth < max_depth:
                        queue.append((target, depth + 1))
                except ValueError:
                    pass

            # 5. Para no retorno da função (pop {.., pc} ou bx lr) se não houver saltos locais óbvios
            if insn.mnemonic == "pop" and "pc" in insn.op_str:
                break
            if insn.mnemonic == "bx" and "lr" in insn.op_str:
                break

    return {
        "vram_refs": sorted(vram_refs),
        "bank06_refs": sorted(bank06_refs),
        "rom_data_refs": sorted(rom_data_refs),
        "ewram_refs": sorted(ewram_refs)[:8],
        "iwram_refs": sorted(iwram_refs)[:8],
        "ioreg_refs": sorted(ioreg_refs),
        "swi_calls": sorted(swi_calls),
        "callees_count": len(callees),
        "visited_funcs_count": len(visited),
    }


def scan_all_bank06_and_vram_xrefs(rom: bytes) -> Dict[str, Any]:
    """
    Varre todas as words na região de código (0x080000C0..0x0806FFFF) procurando
    ponteiros diretos para:
    - Banco #006 (0x08060000..0x0806FFFF)
    - Bancos de Dados/Scripts (0x08070000..0x08760C20)
    - VRAM (0x06000000..0x06017FFF)
    """
    bank06_ptrs = []
    vram_ptrs = []
    rom_asset_table_ptrs = []

    code_end_off = 0x00070000
    for off in range(0xC0, code_end_off, 4):
        val = struct.unpack_from("<I", rom, off)[0]
        rom_addr = GBA_ROM_BASE + off
        if 0x08060000 <= val < 0x08070000:
            bank06_ptrs.append({"pool_addr": f"0x{rom_addr:08X}", "target": f"0x{val:08X}"})
        elif 0x06000000 <= val < 0x06018000:
            vram_ptrs.append({"pool_addr": f"0x{rom_addr:08X}", "target": f"0x{val:08X}"})
        elif 0x08070000 <= val < 0x08760C20 and off < 0x00060000:
            rom_asset_table_ptrs.append({"pool_addr": f"0x{rom_addr:08X}", "target": f"0x{val:08X}"})

    return {
        "bank06_literal_pools": bank06_ptrs,
        "vram_literal_pools": vram_ptrs,
        "rom_asset_literal_pools": rom_asset_table_ptrs,
    }


def main() -> int:
    rom_path = Path("rom/Summon Night - Swordcraft Story (USA).gba")
    rom = rom_path.read_bytes()

    # 1. Analisa o que realmente está no Banco #006 (0x08060000..0x0806FFFF)
    bank06_strings = extract_ascii_samples(rom, 0x08060000, 0x08070000, min_len=6)
    # Também procura onde estão as strings de diálogo/itens em toda a ROM
    all_rom_strings_summary = []
    for bank_idx in range(128):
        b_start = GBA_ROM_BASE + bank_idx * 0x10000
        b_end = b_start + 0x10000
        strs = extract_ascii_samples(rom, b_start, b_end, min_len=10)
        if len(strs) >= 15:
            all_rom_strings_summary.append({
                "bank": f"#{bank_idx:03d}",
                "range": f"0x{b_start:08X}..0x{b_end-1:08X}",
                "string_count": len(strs),
                "examples": [s["sample"] for s in strs[:4]],
            })

    # 2. Analisa cada sub-rotina chamada por AgbMain
    sub_reports = {}
    for addr, phase in AGBMAIN_SUBS:
        key = f"sub_{addr:08X}"
        info = analyze_subroutine_tree(rom, addr, max_depth=3)
        info["phase"] = phase
        sub_reports[key] = info

    # 3. Xrefs diretos de Literal Pools
    xrefs = scan_all_bank06_and_vram_xrefs(rom)

    # Salva tudo em JSON e imprime o relatório
    full_out = {
        "agbmain_subroutines": sub_reports,
        "bank06_strings_sample": bank06_strings[:30],
        "rom_text_banks_detected": all_rom_strings_summary,
        "xref_summary": {
            "bank06_pool_count": len(xrefs["bank06_literal_pools"]),
            "vram_pool_count": len(xrefs["vram_literal_pools"]),
            "rom_asset_pool_count": len(xrefs["rom_asset_literal_pools"]),
            "bank06_pools_sample": xrefs["bank06_literal_pools"][:40],
            "vram_pools_sample": xrefs["vram_literal_pools"][:40],
            "rom_asset_pools_sample": xrefs["rom_asset_literal_pools"][:60],
        },
    }
    Path("extracted/xref_agbmain.json").write_text(json.dumps(full_out, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 95)
    print(" MAPEAMENTO DE SUB-ROTINAS DO AGBMAIN (XREFS: VRAM, BANCO #006, ROM DATA & BIOS SWI)")
    print("=" * 95)
    for name, rep in sub_reports.items():
        has_interesting = (
            rep["vram_refs"] or rep["bank06_refs"] or rep["rom_data_refs"] or rep["swi_calls"] or rep["ioreg_refs"]
        )
        if has_interesting:
            print(f"\n[{name}] (Fase: {rep['phase']} | Funções visitadas: {rep['visited_funcs_count']})")
            if rep["vram_refs"]:
                print(f"  • VRAM (0x06xxxxxx)   : {', '.join(rep['vram_refs'][:6])}")
            if rep["bank06_refs"]:
                print(f"  • Banco #006 (0x0806) : {', '.join(rep['bank06_refs'][:6])}")
            if rep["rom_data_refs"]:
                print(f"  • ROM Assets (0x0807+): {', '.join(rep['rom_data_refs'][:6])}")
            if rep["ioreg_refs"]:
                print(f"  • Hardware I/O        : {', '.join(rep['ioreg_refs'][:6])}")
            if rep["swi_calls"]:
                print(f"  • BIOS SWI            : {', '.join(rep['swi_calls'][:6])}")

    print("\n" + "=" * 95)
    print(" BANCOS COM ALTA DENSIDADE DE STRINGS LEGÍVEIS (TEXTO / ITENS / SCRIPTS)")
    print("=" * 95)
    for tb in all_rom_strings_summary[:20]:
        print(f" {tb['bank']} ({tb['range']}): {tb['string_count']} strings | Ex: {tb['examples'][:2]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
