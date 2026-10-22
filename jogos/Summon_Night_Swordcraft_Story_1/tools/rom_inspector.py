#!/usr/bin/env python3
"""
GBA ROM Inspector & Mapper for Summon Night: Swordcraft Story
=============================================================
Analisa o cabeçalho oficial do GBA (0x00 - 0xBF), decodifica a instrução de
branch do Entry Point (ARM B instruction), calcula o checksum do cabeçalho,
e mapeia a distribuição de entropia, bancos de ponteiros (0x08XXXXXX) e
espaço livre (0xFF / 0x00 padding) ao longo do binário.
"""

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Constantes de Memória do GBA
GBA_ROM_BASE = 0x08000000
NINTENDO_LOGO_CRC = 0x4B89  # CRC16/CCITT aproximado ou soma conhecida dos 156 bytes (0x04..0x9F)


def compute_header_complement(header_bytes: bytes) -> int:
    """
    Calcula o byte de complemento do cabeçalho do GBA (offset 0xBD).
    Fórmula: -(sum(bytes[0xA0..0xBC]) + 0x19) & 0xFF
    """
    chk = sum(header_bytes[0xA0:0xBD])
    return (-(chk + 0x19)) & 0xFF


def decode_arm_branch(word: int, pc_address: int) -> Tuple[str, int]:
    """
    Decodifica uma instrução de salto ARM de 32 bits no Entry Point (0x08000000).
    Formato ARM B / BL: [31:28] Cond | [27:25] 101 | [24] L | [23:0] imm24
    No ARM7TDMI, PC = endereço da instrução atual + 8 bytes (pipeline de 3 estágios).
    """
    cond = (word >> 28) & 0xF
    op = (word >> 25) & 0x7
    link = (word >> 24) & 0x1
    imm24 = word & 0x00FFFFFF

    if op != 0b101:
        return (f"RAW_WORD (0x{word:08X})", pc_address)

    # Extensão de sinal de 24 bits para 32 bits e shift left de 2 (word-aligned)
    if imm24 & 0x00800000:
        imm24 -= 0x01000000
    offset = imm24 << 2
    target = (pc_address + 8 + offset) & 0xFFFFFFFF

    mnemonic = "BL" if link else "B"
    cond_Suffix = "" if cond == 0xE else f"_cond({cond:X})"
    return (f"{mnemonic}{cond_Suffix} 0x{target:08X}", target)


def shannon_entropy(chunk: bytes) -> float:
    """Calcula a entropia de Shannon (0.0 a 8.0 bits/byte) de um bloco de dados."""
    if not chunk:
        return 0.0
    length = len(chunk)
    counts = [0] * 256
    for b in chunk:
        counts[b] += 1
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / length
            entropy -= p * math.log2(p)
    return entropy


def count_rom_pointers(chunk: bytes, rom_size: int) -> int:
    """
    Conta quantas words (32-bit little-endian alinhadas em 4 bytes) apontam
    para a região da ROM0 (0x08000000 .. 0x08000000 + rom_size).
    Excelente heurística para localizar tabelas de ponteiros de script/gráficos e código THUMB literal pools.
    """
    upper_bound = GBA_ROM_BASE + rom_size
    count = 0
    # Desempacota de 4 em 4 bytes
    num_words = len(chunk) // 4
    if num_words == 0:
        return 0
    for (val,) in struct.iter_unpack("<I", chunk[: num_words * 4]):
        if GBA_ROM_BASE <= val < upper_bound:
            count += 1
    return count


def detect_ascii_density(chunk: bytes) -> float:
    """Retorna a proporção de bytes imprimíveis ASCII/Shift-JIS comuns no bloco."""
    if not chunk:
        return 0.0
    printable = sum(1 for b in chunk if (0x20 <= b <= 0x7E) or b in (0x0A, 0x0D))
    return printable / len(chunk)


def find_free_space_regions(rom_data: bytes, min_size: int = 1024) -> List[Dict[str, Any]]:
    """
    Localiza blocos contínuos de espaço livre / padding (0xFF ou 0x00)
    com tamanho mínimo de `min_size` bytes.
    """
    regions = []
    n = len(rom_data)
    i = 0
    while i < n:
        b = rom_data[i]
        if b in (0xFF, 0x00):
            start = i
            while i < n and rom_data[i] == b:
                i += 1
            length = i - start
            if length >= min_size:
                regions.append({
                    "fill_byte": f"0x{b:02X}",
                    "file_offset_start": f"0x{start:08X}",
                    "file_offset_end": f"0x{i - 1:08X}",
                    "rom_addr_start": f"0x{GBA_ROM_BASE + start:08X}",
                    "rom_addr_end": f"0x{GBA_ROM_BASE + i - 1:08X}",
                    "size_bytes": length,
                    "size_kb": round(length / 1024, 2),
                })
        else:
            i += 1
    return regions


def classify_bank(entropy: float, ptr_count: int, ascii_ratio: float, chunk: bytes) -> str:
    """Classifica heuristicamente um banco da ROM (ex: 64 KB)."""
    if all(b == 0xFF for b in chunk):
        return "FREE_SPACE (0xFF)"
    if all(b == 0x00 for b in chunk):
        return "ZERO_PADDING (0x00)"
    if entropy < 1.5:
        return "SPARSE_TABLES / TILEMAP"
    if ptr_count > 600 and 5.2 <= entropy <= 6.8:
        return "CODE (ARM/THUMB) + LITERAL POOLS"
    if ptr_count > 1200:
        return "POINTER_TABLE / SCRIPT_INDEX"
    if ascii_ratio > 0.45:
        return "TEXT / ASCII STRINGS"
    if entropy > 7.2:
        return "COMPRESSED_DATA (LZ77 / HUFFMAN) / AUDIO"
    if 4.0 <= entropy <= 6.2:
        return "GRAPHICS (4BPP/8BPP TILES) / SOUND_SAMPLES"
    return "MIXED_DATA / SCRIPTS"


def inspect_rom(rom_path: Path, bank_size_kb: int = 64, min_free_kb: int = 4) -> Dict[str, Any]:
    rom_data = rom_path.read_bytes()
    rom_size = len(rom_data)

    if rom_size < 0xC0:
        raise ValueError(f"Arquivo muito pequeno ({rom_size} bytes) para ser uma ROM de GBA válida.")

    # 1. Hashes da ROM
    crc32_val = hashlib.new("sha1", rom_data).hexdigest()  # SHA-1
    md5_val = hashlib.md5(rom_data).hexdigest()
    import zlib
    crc32_hex = f"{zlib.crc32(rom_data) & 0xFFFFFFFF:08X}"

    # 2. Parse do Cabeçalho GBA (0x00 - 0xBF)
    entry_word = struct.unpack_from("<I", rom_data, 0x00)[0]
    asm_instr, entry_target = decode_arm_branch(entry_word, GBA_ROM_BASE)

    game_title = rom_data[0xA0:0xAC].decode("ascii", errors="replace").rstrip("\x00")
    game_code = rom_data[0xAC:0xB0].decode("ascii", errors="replace")
    maker_code = rom_data[0xB0:0xB2].decode("ascii", errors="replace")
    fixed_96h = rom_data[0xB2]
    main_unit_code = rom_data[0xB3]
    device_type = rom_data[0xB4]
    software_version = rom_data[0xBC]
    header_checksum = rom_data[0xBD]
    expected_checksum = compute_header_complement(rom_data[:0xC0])

    # 3. Mapeamento de Espaço Livre
    free_regions = find_free_space_regions(rom_data, min_size=min_free_kb * 1024)
    total_free_bytes = sum(r["size_bytes"] for r in free_regions)

    # 4. Mapeamento por Bancos (default: 64 KB = 0x10000 bytes)
    bank_size = bank_size_kb * 1024
    banks = []
    for offset in range(0, rom_size, bank_size):
        chunk = rom_data[offset : offset + bank_size]
        ent = shannon_entropy(chunk)
        ptrs = count_rom_pointers(chunk, rom_size)
        asc = detect_ascii_density(chunk)
        category = classify_bank(ent, ptrs, asc, chunk)
        banks.append({
            "bank_index": offset // bank_size,
            "file_offset": f"0x{offset:08X}",
            "rom_address": f"0x{GBA_ROM_BASE + offset:08X}",
            "entropy": round(ent, 3),
            "rom_pointers_count": ptrs,
            "ascii_density": round(asc, 3),
            "classification": category,
        })

    return {
        "file_info": {
            "filename": rom_path.name,
            "size_bytes": rom_size,
            "size_mb": round(rom_size / (1024 * 1024), 2),
            "crc32": crc32_hex,
            "md5": md5_val,
            "sha1": crc32_val,
        },
        "gba_header": {
            "entry_point_raw": f"0x{entry_word:08X}",
            "entry_point_disasm": asm_instr,
            "entry_point_target_rom": f"0x{entry_target:08X}",
            "entry_point_target_file": f"0x{entry_target - GBA_ROM_BASE:08X}",
            "game_title": game_title,
            "game_code": game_code,
            "maker_code": maker_code,
            "fixed_value_0x96": f"0x{fixed_96h:02X}",
            "main_unit_code": f"0x{main_unit_code:02X}",
            "device_type": f"0x{device_type:02X}",
            "software_version": software_version,
            "header_checksum": f"0x{header_checksum:02X}",
            "expected_checksum": f"0x{expected_checksum:02X}",
            "checksum_valid": header_checksum == expected_checksum,
        },
        "free_space_summary": {
            "min_block_threshold_kb": min_free_kb,
            "total_free_bytes": total_free_bytes,
            "total_free_kb": round(total_free_bytes / 1024, 2),
            "percentage_of_rom": round((total_free_bytes / rom_size) * 100, 2),
            "regions": free_regions,
        },
        "memory_map_banks": banks,
    }


def print_report(report: Dict[str, Any]) -> None:
    fi = report["file_info"]
    hd = report["gba_header"]
    fs = report["free_space_summary"]

    print("=" * 78)
    print(f" GBA ROM INSPECTOR - {fi['filename']}")
    print("=" * 78)
    print(f" Tamanho       : {fi['size_bytes']:,} bytes ({fi['size_mb']} MB)")
    print(f" CRC32 / SHA1  : {fi['crc32']} / {fi['sha1']}")
    print("-" * 78)
    print(" [CABEÇALHO GBA (0x08000000 - 0x080000BF)]")
    print(f" Game Title    : '{hd['game_title']}'")
    print(f" Game Code     : {hd['game_code']} (Maker: {hd['maker_code']}, Ver: v1.{hd['software_version']})")
    print(f" Entry Point   : {hd['entry_point_disasm']} (File Offset: {hd['entry_point_target_file']})")
    chk_status = "OK" if hd["checksum_valid"] else f"INVÁLIDO (Esperado: {hd['expected_checksum']})"
    print(f" Checksum (BDh): {hd['header_checksum']} [{chk_status}]")
    print("-" * 78)
    print(f" [ESPAÇO LIVRE CONTÍNUO (>= {fs['min_block_threshold_kb']} KB)]")
    print(f" Total Livre   : {fs['total_free_kb']} KB ({fs['percentage_of_rom']}% da ROM) em {len(fs['regions'])} região(ões)")
    for r in fs["regions"][:10]:
        print(
            f"   • {r['rom_addr_start']} .. {r['rom_addr_end']} "
            f"(File: {r['file_offset_start']}) | Fill: {r['fill_byte']} | {r['size_kb']:>8.2f} KB"
        )
    if len(fs["regions"]) > 10:
        print(f"   ... (+{len(fs['regions']) - 10} regiões omitidas no resumo)")
    print("-" * 78)
    print(" [RESUMO DE BANCOS DE MEMÓRIA (Primeiros 24 bancos)]")
    print(f" {'Bank':<5} {'ROM Addr':<12} {'Entropy':<8} {'Ptrs':<6} {'ASCII':<6} {'Classificação Heurística'}")
    for b in report["memory_map_banks"][:24]:
        print(
            f" #{b['bank_index']:03d}  {b['rom_address']:<12} {b['entropy']:<8.3f} "
            f"{b['rom_pointers_count']:<6} {b['ascii_density']:<6.2f} {b['classification']}"
        )
    if len(report["memory_map_banks"]) > 24:
        print(f" ... (+{len(report['memory_map_banks']) - 24} bancos adicionais salvos no relatório JSON)")
    print("=" * 78)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspeciona o cabeçalho de uma ROM de GBA e mapeia distribuição de código/dados/espaço livre."
    )
    parser.add_argument(
        "rom",
        nargs="?",
        help="Caminho para o arquivo .gba (se omitido, procura na pasta rom/)",
    )
    parser.add_argument(
        "--bank-kb",
        type=int,
        default=64,
        help="Tamanho de cada banco de análise em KB (padrão: 64 KB)",
    )
    parser.add_argument(
        "--min-free-kb",
        type=int,
        default=4,
        help="Tamanho mínimo em KB para reportar bloco de espaço livre (padrão: 4 KB)",
    )
    parser.add_argument(
        "--json-out",
        type=str,
        default="extracted/rom_map.json",
        help="Caminho para salvar o mapeamento detalhado em JSON",
    )

    args = parser.parse_args()

    rom_path: Path | None = None
    if args.rom:
        rom_path = Path(args.rom)
    else:
        rom_dir = Path("rom")
        if rom_dir.exists():
            gba_files = sorted(rom_dir.glob("*.gba"))
            if gba_files:
                rom_path = gba_files[0]

    if not rom_path or not rom_path.exists():
        print(
            "[!] Nenhuma ROM (.gba) encontrada.\n"
            "    Coloque a ROM de 'Summon Night: Swordcraft Story' na pasta 'rom/'\n"
            "    ou execute: python tools/rom_inspector.py caminho/para/rom.gba",
            file=sys.stderr,
        )
        return 1

    report = inspect_rom(rom_path, bank_size_kb=args.bank_kb, min_free_kb=args.min_free_kb)
    print_report(report)

    if args.json_out:
        out_path = Path(args.json_out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[+] Mapeamento completo exportado para: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
