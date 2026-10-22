#!/usr/bin/env python3
"""
Valida todos os 14 opcodes com argumentos `u16` contra as fronteiras de instrução
de todos os 1.189 scripts únicos do Archive #2, e lista as strings de 0x0212, 0x021D, 0x0228 e 0x0229.
"""

import struct
from pathlib import Path
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB
from archive_extractor import parse_archive_table, decompress_gba_lz77
from sjis_script_dumper import decode_sjis_u16

GBA_ROM_BASE = 0x08000000

VM_TABLES = [
    (0x0000, 0x081DD5C8, 0x40),
    (0x0100, 0x081F57F8, 0xB0),
    (0x0200, 0x081F5AB8, 0x58),
    (0x0300, 0x081F5C18, 0x30),
    (0x0400, 0x081F5CD8, 0x35),
]

CANDIDATE_OFFSET_OPCODES = {
    0x0002,
    0x0003,
    0x0007,
    0x0009,
    0x010B,
    0x011E,
    0x0162,
    0x0166,
    0x016C,
    0x0185,
    0x0186,
    0x018F,
    0x0221,
    0x0305,
}


def build_opcode_spec_table(rom: bytes) -> dict[int, list[str]]:
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    specs: dict[int, list[str]] = {}
    for prefix, tbl_addr, count in VM_TABLES:
        off = tbl_addr - GBA_ROM_BASE
        for i in range(count):
            ptr = struct.unpack_from("<I", rom, off + i * 4)[0]
            if not (0x08000000 <= ptr < 0x08800000):
                continue
            op = prefix | i
            if op in (0x0212, 0x0218, 0x021D, 0x0220):
                specs[op] = ["STR"]
                continue
            elif op == 0x0221:
                specs[op] = ["OFFSET", "STR"]
                continue
            elif op in (0x0228, 0x0229):
                specs[op] = ["EXPR", "STR"]
                continue
            elif op == 0x0223:
                specs[op] = ["EXPR"] * 5
                continue

            fn_addr = ptr & ~1
            fn_off = fn_addr - GBA_ROM_BASE
            arg_list = []
            for insn in md.disasm(rom[fn_off : fn_off + 1200], fn_addr):
                if insn.mnemonic == "bl":
                    if insn.op_str == "#0x800cef4":
                        arg_list.append("EXPR")
                    elif insn.op_str == "#0x800cec8":
                        arg_list.append("OFFSET" if op in CANDIDATE_OFFSET_OPCODES else "U16")
                if insn.mnemonic == "bx" and any(r in insn.op_str for r in ("lr", "r0", "r1", "r2", "r3")):
                    break
                if insn.mnemonic == "pop" and "pc" in insn.op_str:
                    break
            specs[op] = arg_list
    return specs


def consume_expr(data: bytes, pos: int) -> int:
    n = len(data)
    while pos < n:
        tok = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if tok == 0x0000:
            return pos
        elif tok in (0x0001, 0x0002, 0x0003):
            pos += 2
        elif 0x0080 <= tok <= 0x0091:
            pass
        else:
            raise ValueError(f"Token desconhecido 0x{tok:04X}")
    raise ValueError("EOF")


def consume_str(data: bytes, pos: int) -> int:
    n = len(data)
    while pos < n:
        ch = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if ch == 0x0000:
            return pos
    raise ValueError("EOF")


def main():
    rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
    specs = build_opcode_spec_table(rom)
    entries = parse_archive_table(rom, 0x085C10DC, 0x0870771C)

    seen_offsets = set()
    op_stats = {op: {"valid_target": 0, "invalid_target": 0, "samples": []} for op in CANDIDATE_OFFSET_OPCODES}
    extra_strings = {0x0212: [], 0x021D: [], 0x0228: [], 0x0229: []}

    for idx, e in enumerate(entries):
        rom_off = int(e["rom_addr"], 16) - GBA_ROM_BASE
        if rom_off in seen_offsets:
            continue
        seen_offsets.add(rom_off)
        res = decompress_gba_lz77(rom, rom_off)
        if not res:
            continue
        data, _ = res
        if data[:4] != b"PSI3":
            continue

        pos = 0x10
        n = len(data)
        insn_starts = set()
        recorded_offsets = []

        while pos < n:
            insn_starts.add(pos)
            op = struct.unpack_from("<H", data, pos)[0]
            if op == 0x0000:
                break
            pos += 2
            for arg_type in specs[op]:
                if arg_type == "OFFSET":
                    val = struct.unpack_from("<H", data, pos)[0]
                    recorded_offsets.append((op, val))
                    pos += 2
                elif arg_type == "U16":
                    pos += 2
                elif arg_type == "EXPR":
                    pos = consume_expr(data, pos)
                elif arg_type == "STR":
                    str_start = pos
                    pos = consume_str(data, pos)
                    if op in extra_strings and len(extra_strings[op]) < 8:
                        chars = []
                        for p in range(str_start, pos - 2, 2):
                            hw = struct.unpack_from("<H", data, p)[0]
                            chars.append(decode_sjis_u16(hw) or f"<0x{hw:04X}>")
                        extra_strings[op].append((idx, "".join(chars)))

        for op, val in recorded_offsets:
            target_pos = 0x10 + (val & 0xFFFE)
            if target_pos in insn_starts:
                op_stats[op]["valid_target"] += 1
            else:
                op_stats[op]["invalid_target"] += 1
                if len(op_stats[op]["samples"]) < 5:
                    op_stats[op]["samples"].append((idx, hex(val), hex(target_pos), hex(len(data))))

    print("=== 1. VALIDAÇÃO DE TARGET_OFFSET POR OPCODE ===")
    for op in sorted(CANDIDATE_OFFSET_OPCODES):
        st = op_stats[op]
        print(
            f"  Opcode 0x{op:04X}: valid_insn_boundary={st['valid_target']:5d} | "
            f"non_boundary={st['invalid_target']:4d} | samples={st['samples']}"
        )

    print("\n=== 2. AMOSTRAS DE STRINGS EM 0x0212, 0x021D, 0x0228, 0x0229 ===")
    for op, samples in extra_strings.items():
        print(f"  Opcode 0x{op:04X} ({len(samples)} amostras):")
        for s_idx, txt in samples:
            print(f"    [script_{s_idx:04d}] {txt!r}")


if __name__ == "__main__":
    main()
