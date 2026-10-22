#!/usr/bin/env python3
"""
GBA Archive FS & LZ77 Extractor + Script/Text Inspector
Summon Night: Swordcraft Story (USA) [AB4E]
=======================================================
Usa exatamente a fórmula descompilada de Archive_GetFileRomPtr (0x08006FC4) e
Archive_GetFileSize (0x08006FE4) para listar, extrair e descomprimir (GBA BIOS
LZ77, header 0x10) os sub-arquivos dos 4 Archives principais da ROM:
  - Archive 0: 0x081FCA8C
  - Archive 1: 0x08380CCC
  - Archive 2: 0x085C10DC (Scripts de Eventos e Diálogos)
  - Archive 3: 0x0870771C (Fontes / Menus / UI)
"""

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

GBA_ROM_BASE = 0x08000000

ARCHIVE_BASES = [
    (0, 0x081FCA8C, 0x08380CCC, "Archive0_Maps_Tilesets"),
    (1, 0x08380CCC, 0x085C10DC, "Archive1_Sprites_Battle"),
    (2, 0x085C10DC, 0x0870771C, "Archive2_Scripts_Dialogues"),
    (3, 0x0870771C, 0x08760C21, "Archive3_UI_Fonts_Menus"),
]


def decompress_gba_lz77(data: bytes, offset: int = 0, max_out: int = 0x80000) -> Optional[ Tuple[bytes, int] ]:
    """
    Descomprime um bloco no formato LZ77 padrão da BIOS do GBA (SWI 0x11 / 0x12).
    Header de 32 bits: [7:0] = 0x10 (magic LZ77), [31:8] = tamanho descomprimido.
    Retorna (decompressed_bytes, compressed_bytes_consumed) ou None se inválido.
    """
    if offset + 4 > len(data):
        return None
    header = struct.unpack_from("<I", data, offset)[0]
    if (header & 0xFF) != 0x10:
        return None

    decomp_size = header >> 8
    if decomp_size == 0 or decomp_size > max_out:
        return None

    out = bytearray()
    src = offset + 4
    n = len(data)

    while len(out) < decomp_size and src < n:
        flags = data[src]
        src += 1
        for bit in range(7, -1, -1):
            if len(out) >= decomp_size:
                break
            if flags & (1 << bit):
                # Bloco comprimido (2 bytes big-endian): disp (12 bits) e length (4 bits + 3)
                if src + 1 >= n:
                    return None
                b1 = data[src]
                b2 = data[src + 1]
                src += 2
                length = (b1 >> 4) + 3
                disp = (((b1 & 0x0F) << 8) | b2) + 1
                if disp > len(out):
                    return None
                for _ in range(length):
                    if len(out) >= decomp_size:
                        break
                    out.append(out[-disp])
            else:
                # Byte literal
                if src >= n:
                    return None
                out.append(data[src])
                src += 1

    if len(out) != decomp_size:
        return None
    return (bytes(out), src - offset)


def parse_archive_table(rom: bytes, base_rom_addr: int, limit_rom_addr: int) -> List[Dict[str, Any]]:
    """
    Lê a tabela de entradas de um Archive em `base_rom_addr`:
      header +0x00: word0, +0x04: word1
      entry[i] @ base + 8 + i*8:
        u32 offset_units_16 (byte_offset = offset_units_16 << 4)
        u32 size_units_16   (byte_size   = size_units_16 << 4)
    """
    base_off = base_rom_addr - GBA_ROM_BASE
    limit_off = limit_rom_addr - GBA_ROM_BASE
    max_archive_bytes = limit_off - base_off

    hdr0, hdr1 = struct.unpack_from("<II", rom, base_off)
    # O primeiro offset indica onde começa o primeiro arquivo de dados (fim da tabela de índice!)
    first_off_units, first_size_units = struct.unpack_from("<II", rom, base_off + 8)
    first_byte_off = first_off_units << 4

    # Número máximo de entradas antes do início do primeiro arquivo de dados
    max_entries = (first_byte_off - 8) // 8 if first_byte_off >= 16 else 0

    entries = []
    for idx in range(max_entries):
        ent_off = base_off + 8 + idx * 8
        off_u16, size_u16 = struct.unpack_from("<II", rom, ent_off)
        byte_off = off_u16 << 4
        byte_size = size_u16 << 4

        if byte_off == 0 and byte_size == 0:
            continue
        if base_off + byte_off >= len(rom) or base_off + byte_off + byte_size > len(rom):
            break

        file_rom_addr = base_rom_addr + byte_off
        file_rom_off = base_off + byte_off
        raw_head = rom[file_rom_off : file_rom_off + 16]
        is_lz77 = len(raw_head) >= 4 and raw_head[0] == 0x10
        decomp_len = (struct.unpack_from("<I", raw_head, 0)[0] >> 8) if is_lz77 else 0

        entries.append({
            "index": idx,
            "rom_addr": f"0x{file_rom_addr:08X}",
            "file_offset": file_rom_off,
            "compressed_size": byte_size,
            "is_lz77": is_lz77,
            "lz77_decomp_size": decomp_len if is_lz77 else None,
            "head_hex": raw_head[:8].hex().upper(),
        })

    return entries


def extract_printable_strings(buf: bytes, min_len: int = 4) -> List[Dict[str, Any]]:
    """Extrai sequências ASCII imprimíveis de um buffer descomprimido."""
    strings = []
    i = 0
    n = len(buf)
    while i < n:
        if 0x20 <= buf[i] <= 0x7E:
            start = i
            chars = []
            while i < n and (0x20 <= buf[i] <= 0x7E or buf[i] in (0x09, 0x0A, 0x0D)):
                chars.append(chr(buf[i]))
                i += 1
            s = "".join(chars).strip()
            if len(s) >= min_len:
                strings.append({"offset": f"0x{start:04X}", "text": s})
        else:
            i += 1
    return strings


def inspect_script_structure(decomp: bytes) -> Dict[str, Any]:
    """
    Analisa a estrutura interna de um script descomprimido do Archive 2.
    Sabemos por `sub_0800CC70` e `sub_0800CE28` que o bytecode começa em `workBuffer + 0x10`
    (ou `workBuffer + 0x10 + (offset & 0xFFFE)`), e os primeiros 16 bytes (`0x00..0x0F`)
    formam o cabeçalho do arquivo de script.
    """
    if len(decomp) < 16:
        return {"header_words": [], "strings": []}
    hdr_words = list(struct.unpack_from("<IIII", decomp, 0))
    strings = extract_printable_strings(decomp, min_len=4)
    return {
        "decomp_size": len(decomp),
        "header_u32_hex": [f"0x{w:08X}" for w in hdr_words],
        "header_u16_hex": [f"0x{h:04X}" for h in struct.unpack_from("<8H", decomp, 0)],
        "first_32_bytes_after_0x10": decomp[0x10:0x30].hex().upper(),
        "ascii_string_count": len(strings),
        "sample_strings": strings[:25],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extrator de Archives e LZ77 de Summon Night: Swordcraft Story")
    parser.add_argument(
        "--rom",
        default="rom/Summon Night - Swordcraft Story (USA).gba",
        help="Caminho da ROM",
    )
    parser.add_argument(
        "--extract-archive2",
        type=int,
        default=15,
        help="Quantos arquivos iniciais do Archive 2 descomprimir e salvar em extracted/archive2/",
    )
    args = parser.parse_args()

    rom_path = Path(args.rom)
    rom = rom_path.read_bytes()

    summary: Dict[str, Any] = {"archives": {}}
    print("=" * 92)
    print(" SUMMON NIGHT: SWORDCRAFT STORY - ARCHIVE FILE SYSTEM & LZ77 INSPECTOR")
    print("=" * 92)

    for arc_id, base_addr, limit_addr, arc_name in ARCHIVE_BASES:
        entries = parse_archive_table(rom, base_addr, limit_addr)
        lz77_count = sum(1 for e in entries if e["is_lz77"])
        print(
            f" • Archive #{arc_id} ({arc_name:<26}) @ 0x{base_addr:08X} : "
            f"{len(entries):>4} arquivos | {lz77_count:>4} com header LZ77 (0x10)"
        )
        summary["archives"][arc_name] = {
            "archive_id": arc_id,
            "base_rom_addr": f"0x{base_addr:08X}",
            "total_files": len(entries),
            "lz77_files": lz77_count,
            "first_20_entries": entries[:20],
        }

    # Agora descomprime e inspeciona os arquivos do Archive 2 (Scripts/Eventos) e procura bancos de texto
    arc2_entries = parse_archive_table(rom, 0x085C10DC, 0x0870771C)
    out_dir = Path("extracted/archive2_scripts")
    out_dir.mkdir(parents=True, exist_ok=True)

    inspected_scripts = []
    scripts_with_most_text = []

    print("-" * 92)
    print(f" Descomprimindo todos os {len(arc2_entries)} arquivos do Archive #2 (0x085C10DC) para análise...")

    success_decomp = 0
    for ent in arc2_entries:
        idx = ent["index"]
        f_off = ent["file_offset"]
        res = decompress_gba_lz77(rom, f_off)
        if res is not None:
            decomp_bytes, comp_used = res
            success_decomp += 1
            info = inspect_script_structure(decomp_bytes)
            info["file_index"] = idx
            info["rom_addr"] = ent["rom_addr"]
            info["compressed_size"] = ent["compressed_size"]

            if idx < args.extract_archive2:
                bin_path = out_dir / f"script_{idx:04d}.bin"
                bin_path.write_bytes(decomp_bytes)
                inspected_scripts.append(info)

            if info["ascii_string_count"] >= 5:
                scripts_with_most_text.append({
                    "file_index": idx,
                    "rom_addr": ent["rom_addr"],
                    "decomp_size": len(decomp_bytes),
                    "ascii_string_count": info["ascii_string_count"],
                    "header_u16": info["header_u16_hex"][:4],
                    "sample_strings": info["sample_strings"][:8],
                })
                # Salva também os primeiros 10 arquivos ricos em texto
                if len(scripts_with_most_text) <= 10:
                    bin_path = out_dir / f"script_{idx:04d}_text.bin"
                    bin_path.write_bytes(decomp_bytes)

    print(f" [+] {success_decomp}/{len(arc2_entries)} arquivos do Archive #2 descomprimidos com sucesso via LZ77!")
    print(f" [+] {len(scripts_with_most_text)} arquivos contêm >= 5 strings ASCII legíveis.")
    print("-" * 92)

    # Também verifica Archive 3 (0x0870771C) e Archive 0 (0x081FCA8C) em busca de textos/diálogos
    for arc_id, base_addr, limit_addr, arc_name in [(0, 0x081FCA8C, 0x08380CCC, "Archive0"), (1, 0x08380CCC, 0x085C10DC, "Archive1"), (3, 0x0870771C, 0x08760C21, "Archive3")]:
        ents = parse_archive_table(rom, base_addr, limit_addr)
        text_files = []
        for ent in ents:
            res = decompress_gba_lz77(rom, ent["file_offset"])
            if res:
                d_bytes, _ = res
                strs = extract_printable_strings(d_bytes, min_len=6)
                # Filtra strings que parecem palavras reais em inglês (espaços + letras)
                eng_strs = [s for s in strs if " " in s["text"] and any(c.isalpha() for c in s["text"])]
                if len(eng_strs) >= 3:
                    text_files.append({
                        "file_index": ent["index"],
                        "rom_addr": ent["rom_addr"],
                        "decomp_size": len(d_bytes),
                        "eng_string_count": len(eng_strs),
                        "samples": eng_strs[:5],
                    })
        summary["archives"][f"{arc_name}_text_candidates"] = text_files[:15]
        print(f" • {arc_name}: {len(text_files)} sub-arquivos LZ77 contendo frases em inglês com espaços.")

    summary["archive2_first_scripts"] = inspected_scripts
    summary["archive2_text_rich_scripts"] = scripts_with_most_text[:30]

    json_path = Path("extracted/archive_inspection.json")
    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n[+] Relatório detalhado salvo em: {json_path}")

    if scripts_with_most_text:
        print("\n[AMOSTRA DE ARQUIVOS DO ARCHIVE #2 COM STRINGS]")
        for item in scripts_with_most_text[:8]:
            print(
                f"  File #{item['file_index']:04d} ({item['rom_addr']}, {item['decomp_size']} B) "
                f"Hdr={item['header_u16']} -> {[s['text'][:40] for s in item['sample_strings'][:3]]}"
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
