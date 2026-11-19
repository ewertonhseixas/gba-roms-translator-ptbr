#!/usr/bin/env python3
"""
ROM Feature Detector — Protocolo de Extração para Tradução de ROMs
=================================================================
Realiza a varredura e fingerprint de uma ROM (com foco inicial em GBA e
extensível para outros consoles retro), detectando:
  - Metadados do cabeçalho da ROM (Title, Game Code, Maker, Checksum)
  - Assinaturas de vídeo cinemático / FMV (Mobiclip MOC4/MOC5, Actimagine)
  - Compressões padrão de BIOS (LZ77 0x10, Huffman 0x20/0x30, RLE 0x40)
  - Densidade de texto e estimativa de tabelas de ponteiros (32-bit GBA)
  - Gera um relatório de auditoria inicial para orientar a extração
"""

import os
import sys
import struct
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def detect_gba_header(rom_bytes: bytes) -> Dict[str, Any]:
    """Decodifica os metadados do cabeçalho oficial de uma ROM GBA (0x00 a 0xC0)."""
    if len(rom_bytes) < 0xC0:
        return {"valid": False, "error": "Arquivo menor que o cabeçalho GBA (192 bytes)"}

    # Título do jogo (0xA0 - 0xAB: 12 bytes ASCII)
    title_raw = rom_bytes[0xA0:0xAC]
    title = title_raw.decode("ascii", errors="replace").strip("\x00")

    # Game code (0xAC - 0xAF: 4 bytes ASCII)
    game_code_raw = rom_bytes[0xAC:0xB0]
    game_code = game_code_raw.decode("ascii", errors="replace").strip("\x00")

    # Maker code (0xB0 - 0xB1: 2 bytes ASCII)
    maker_code = rom_bytes[0xB0:0xB2].decode("ascii", errors="replace").strip("\x00")

    # Fixed value (0xB2: deve ser 0x96)
    fixed_val = rom_bytes[0xB2]

    # Main unit code (0xB3)
    main_unit = rom_bytes[0xB3]

    # Device type (0xB4)
    device_type = rom_bytes[0xB4]

    # Software version (0xBC)
    version = rom_bytes[0xBC]

    # Complement check (0xBD)
    comp_check = rom_bytes[0xBD]

    # Checksum calculation: -(sum of bytes from 0xA0 to 0xBC) - 0x19 modulo 256
    chk_sum = 0
    for b in rom_bytes[0xA0:0xBD]:
        chk_sum = (chk_sum + b) & 0xFF
    calculated_comp = (-(chk_sum + 0x19)) & 0xFF
    is_valid_gba = (fixed_val == 0x96) and (comp_check == calculated_comp)

    return {
        "valid": is_valid_gba,
        "platform": "Game Boy Advance (GBA)",
        "title": title or "DESCONHECIDO",
        "game_code": game_code or "----",
        "maker_code": maker_code or "--",
        "version": f"v1.{version}",
        "complement_check": hex(comp_check),
        "complement_valid": comp_check == calculated_comp,
    }


def scan_for_video_signatures(rom_bytes: bytes) -> List[Dict[str, Any]]:
    """Varre a ROM em busca de assinaturas conhecidas de codecs de vídeo (Mobiclip, Actimagine, etc)."""
    signatures = [
        (b"MOC5", "Mobiclip Video Codec v5 (FMV de alta qualidade para GBA)"),
        (b"MOC4", "Mobiclip Video Codec v4 (GBA Video / Cutscenes)"),
        (b"MoSys", "Mobiclip Motion System Container"),
        (b"Actimagine", "Actimagine Video Engine Codec"),
        (b"VXDS", "Nintendo DS / GBA VX Video Stream"),
    ]

    detections = []
    for sig, desc in signatures:
        offset = 0
        while True:
            pos = rom_bytes.find(sig, offset)
            if pos == -1:
                break
            detections.append({
                "signature": sig.decode("ascii", errors="ignore"),
                "description": desc,
                "offset_hex": f"0x{pos:08X}",
                "offset_dec": pos,
            })
            offset = pos + len(sig)
            if len(detections) >= 20:  # Limita para não inundar
                break

    return detections


def scan_for_bios_compressions(rom_bytes: bytes, max_samples: int = 10) -> Dict[str, Any]:
    """Escaneia blocos com cabeçalhos padrão da BIOS GBA (LZ77 0x10, Huffman 0x20/0x30, RLE 0x40)."""
    lz77_count = 0
    huffman_count = 0
    rle_count = 0
    sample_lz77 = []

    rom_len = len(rom_bytes)
    # Pula os primeiros 0xC0 bytes do cabeçalho
    for pos in range(0xC0, rom_len - 8, 4):
        b0 = rom_bytes[pos]
        if b0 == 0x10:
            # Descomprime tamanho de 24 bits
            decomp_size = rom_bytes[pos + 1] | (rom_bytes[pos + 2] << 8) | (rom_bytes[pos + 3] << 16)
            if 64 <= decomp_size <= 256 * 1024:
                lz77_count += 1
                if len(sample_lz77) < max_samples:
                    sample_lz77.append((f"0x{pos:08X}", decomp_size))
        elif b0 in (0x20, 0x30):
            huffman_count += 1
        elif b0 == 0x40:
            rle_count += 1

    return {
        "lz77_blocks_estimated": lz77_count,
        "huffman_blocks_estimated": huffman_count,
        "rle_blocks_estimated": rle_count,
        "sample_lz77": sample_lz77,
    }


def scan_for_pointer_tables(rom_bytes: bytes, min_sequence: int = 8) -> List[Dict[str, Any]]:
    """Localiza tabelas contínuas de ponteiros de 32 bits (0x08000000 - 0x09FFFFFF) na ROM."""
    tables = []
    rom_len = len(rom_bytes)
    max_addr = 0x08000000 + rom_len

    i = 0xC0
    while i < rom_len - (min_sequence * 4):
        ptrs = []
        curr = i
        while curr < rom_len - 4:
            val = struct.unpack_from("<I", rom_bytes, curr)[0]
            if 0x08000000 <= val < max_addr:
                ptrs.append(val)
                curr += 4
            else:
                break

        if len(ptrs) >= min_sequence:
            tables.append({
                "start_offset": f"0x{i:08X}",
                "end_offset": f"0x{curr:08X}",
                "count": len(ptrs),
                "first_target": f"0x{ptrs[0]:08X}",
                "last_target": f"0x{ptrs[-1]:08X}",
            })
            i = curr
        else:
            i += 4

    return tables


def generate_rom_audit_report(rom_path: Path, output_md: Path):
    """Gera o relatório de auditoria e fingerprint da ROM em formato Markdown."""
    rom_bytes = rom_path.read_bytes()
    rom_size = len(rom_bytes)
    rom_size_mb = rom_size / (1024 * 1024)

    header = detect_gba_header(rom_bytes)
    videos = scan_for_video_signatures(rom_bytes)
    compressions = scan_for_bios_compressions(rom_bytes)
    tables = scan_for_pointer_tables(rom_bytes, min_sequence=16)

    md = f"""# 🔍 Relatório de Auditoria e Fingerprint da ROM
**Arquivo Analisado:** `{rom_path.name}`  
**Plataforma Detectada:** {header.get('platform', 'Desconhecida')}  
**Tamanho do Arquivo:** {rom_size:,} bytes ({rom_size_mb:.2f} MB)  
**Validação de Cabeçalho GBA:** {"✅ Válido" if header.get('valid') else "⚠️ Não Padrão / Inválido"}  

---

## 🏷️ 1. Metadados Oficiais da ROM

| Campo do Cabeçalho | Valor Identificado | Significado |
| :--- | :--- | :--- |
| **Título do Jogo** | `{header.get('title')}` | Nome gravado no registro interno do cartucho |
| **Game Code (Serial)** | `{header.get('game_code')}` | Código de 4 letras da Nintendo |
| **Maker Code** | `{header.get('maker_code')}` | ID da publicadora/desenvolvedora |
| **Versão de Software** | `{header.get('version')}` | Revisão oficial do cartucho |
| **Complement Check** | `{header.get('complement_check')}` | {"✅ Checksum íntegro" if header.get('complement_valid') else "❌ Checksum corrompido"} |

---

## 🎬 2. Auditoria de Vídeos e FMVs

"""

    if not videos:
        md += "> ✅ **Nenhum codec de vídeo dedicado detectado.** A ROM utiliza gráficos nativos de sprites e tilesets para animações e cinemáticas.\n\n"
    else:
        md += "> ⚠️ **ATENÇÃO! Fluxo de vídeo ou FMV identificado na ROM!**\n\n"
        md += "| Assinatura | Offset na ROM | Descrição Técnica |\n"
        md += "| :---: | :--- | :--- |\n"
        for v in videos:
            md += f"| `{v['signature']}` | `{v['offset_hex']}` | {v['description']} |\n"
        md += "\n**Diretriz:** Notificar o tradutor para estudo de viabilidade de legendagem (hardsub vs softsub overlay).\n\n"

    md += f"""---

## 📦 3. Compressões de Dados e Gráficos da BIOS

| Tipo de Compressão | Blocos Estimados na ROM | Observações |
| :--- | :---: | :--- |
| **BIOS LZ77 (`0x10`)** | `{compressions.get('lz77_blocks_estimated', 0)}` | Padrão mais comum para tilesets, sprites e mapas |
| **Huffman (`0x20`/`0x30`)** | `{compressions.get('huffman_blocks_estimated', 0)}` | Usado ocasionalmente para fontes e dados densos |
| **RLE (`0x40`)** | `{compressions.get('rle_blocks_estimated', 0)}` | Compressão linear simples de repetição |

---

## 🎯 4. Tabelas de Ponteiros Identificadas (Amostra das Maiores)

Foram localizadas **{len(tables)} tabelas sequenciais de ponteiros de 32-bit** na ROM. As 10 mais extensas:

| Offset Inicial | Offset Final | Qtd. Ponteiros | Primeiro Destino | Último Destino |
| :--- | :--- | :---: | :--- | :--- |
"""

    sorted_tables = sorted(tables, key=lambda t: t["count"], reverse=True)
    for t in sorted_tables[:10]:
        md += f"| `{t['start_offset']}` | `{t['end_offset']}` | **{t['count']}** | `{t['first_target']}` | `{t['last_target']}` |\n"

    output_md.write_text(md, encoding="utf-8")
    print(f"✅ Relatório de auditoria gerado em: {output_md}")


def main():
    parser = argparse.ArgumentParser(description="Detector de recursos e fingerprint de ROMs")
    parser.add_argument("rom", help="Caminho do arquivo da ROM (.gba)")
    parser.add_argument("--out", "-o", default=None, help="Caminho do relatório de auditoria Markdown")

    args = parser.parse_args()
    rom_file = Path(args.rom)

    if not rom_file.exists():
        print(f"❌ Arquivo de ROM não encontrado: {rom_file}")
        sys.exit(1)

    out_file = Path(args.out) if args.out else rom_file.parent / f"relatorio-auditoria-{rom_file.stem}.md"
    generate_rom_audit_report(rom_file, out_file)


if __name__ == "__main__":
    main()
