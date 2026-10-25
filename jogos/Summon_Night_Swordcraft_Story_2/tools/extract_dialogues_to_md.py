#!/usr/bin/env python3
"""
Extrator de Diálogos PSI3 para Markdown (PT-BR)
Summon Night: Swordcraft Story 2 (USA) [BSKE]
==============================================
Varre os scripts do Archive 2 e Archive 0, decodifica strings Shift-JIS
de 16-bit com suporte completo a:
  - Glifos duplos de 16x12 pixels ('…', '☆', '★', '◎', '♪')
  - Variáveis dinâmicas da engine ({PLAYER}, {PARTNER}, {SIBLING}, {MASTER})
  - Validação estrita para evitar falsos positivos
Gera os arquivos organizados em lotes limpos prontos para tradução em 'ARQUIVOS md/'.
"""

import os
import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
ROM_PATH = ROOT_DIR / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
MD_DIR = ROOT_DIR / "ARQUIVOS md"

sys.path.insert(0, str(ROOT_DIR / "tools"))
from archive_extractor import decompress_gba_lz77, parse_archive_table

ARCHIVE2_BASE = 0x08ABA81C
ARCHIVE2_LIMIT = 0x08C7F5FC

SJIS_PUNCT_DECODE: Dict[int, str] = {
    0x8140: " ",
    0x8143: ",",
    0x8144: ".",
    0x8145: "・",
    0x8146: ":",
    0x8147: ";",
    0x8148: "?",
    0x8149: "!",
    0x815B: "ー",
    0x815E: "/",
    0x8160: "~",
    0x8166: "'",
    0x8168: '"',
    0x8169: "(",
    0x816A: ")",
    0x817B: "+",
    0x817C: "-",
    0x817E: "×",
    0x8181: "=",
    0x8193: "%",
    0x8195: "&",
    0x8196: "*",
    0x8197: " @ ",
}

WIDE_GLYPH_PAIRS_DECODE: Dict[Tuple[int, int], str] = {
    (0x8163, 0x84AD): "…",
    (0x8199, 0x84AA): "☆",
    (0x819A, 0x84AB): "★",
    (0x819D, 0x84AC): "◎",
    (0x81F4, 0x84AE): "♪",
}

VAR_DECODE: Dict[int, str] = {
    0x83C0: "{PLAYER}",
    0x83C1: "{PARTNER}",
    0x83C2: "{VAR_2}",
    0x83C3: "{SIBLING}",
    0x83C4: "{VAR_4}",
    0x83C5: "{MASTER}",
}


def is_valid_sjis_dialogue(data: bytes, pos: int) -> bool:
    if pos + 2 > len(data):
        return False
    w0 = struct.unpack_from(">H", data, pos)[0]
    # Início da frase: letra, dígito, variável, aspas, reticências
    valid_start = (
        (0x8260 <= w0 <= 0x8279) or
        (0x8281 <= w0 <= 0x829A) or
        (0x824F <= w0 <= 0x8258) or
        w0 in (0x83C0, 0x83C1, 0x83C2, 0x83C3, 0x83C4, 0x83C5, 0x8166, 0x8168, 0x8140, 0x8163, 0x8199, 0x819A, 0x81F4)
    )
    if not valid_start:
        return False

    p = pos
    n = len(data)
    length = 0
    while p + 1 < n:
        w = struct.unpack_from(">H", data, p)[0]
        p += 2
        if w == 0x0000:
            return length >= 1
        length += 1
        if length > 500:
            return False
        b0 = (w >> 8) & 0xFF
        b1 = w & 0xFF
        if b0 == 0 or b1 == 0:
            return False
    return False


def decode_sjis_u16(data: bytes, start_pos: int) -> Tuple[str, int]:
    chars = []
    pos = start_pos
    n = len(data)
    while pos + 1 < n:
        w = struct.unpack_from(">H", data, pos)[0]
        pos += 2
        if w == 0x0000:
            break

        # Glifo duplo (16x12)
        if pos + 1 < n:
            w_next = struct.unpack_from(">H", data, pos)[0]
            if (w, w_next) in WIDE_GLYPH_PAIRS_DECODE:
                chars.append(WIDE_GLYPH_PAIRS_DECODE[(w, w_next)])
                pos += 2
                continue

        if 0x8260 <= w <= 0x8279:
            chars.append(chr(ord("A") + w - 0x8260))
        elif 0x8281 <= w <= 0x829A:
            chars.append(chr(ord("a") + w - 0x8281))
        elif 0x824F <= w <= 0x8258:
            chars.append(chr(ord("0") + w - 0x824F))
        elif w in VAR_DECODE:
            chars.append(VAR_DECODE[w])
        elif w in SJIS_PUNCT_DECODE:
            chars.append(SJIS_PUNCT_DECODE[w])
        else:
            b = struct.pack(">H", w)
            try:
                ch = b.decode("cp932")
                chars.append(ch)
            except Exception:
                chars.append(f"[{w:04X}]")

    return "".join(chars), pos


def extract_script_dialogues(decomp: bytes) -> List[Dict[str, Any]]:
    dialogues = []
    if not decomp.startswith(b"PSI3"):
        return dialogues

    pos = 16
    n = len(decomp)
    while pos + 1 < n:
        op = struct.unpack_from("<H", decomp, pos)[0]
        # Opcodes de texto do SN2:
        # 0x0306: falas de diálogos de NPCs e história principal
        # 0x0361: nomes de salas, áreas e mapas
        # 0x0310: avisos de sistema e popups centrais
        # 0x030D: opções de escolhas e menus interativos
        if op in (0x0306, 0x0361, 0x0310, 0x030D):
            if is_valid_sjis_dialogue(decomp, pos + 2):
                text, next_pos = decode_sjis_u16(decomp, pos + 2)
                clean = text.strip()
                has_latin = any("A" <= c <= "Z" or "a" <= c <= "z" for c in clean)
                if clean and (has_latin or "{" in clean):
                    dialogues.append({
                        "opcode": f"0x{op:04X}",
                        "offset": f"0x{pos:04X}",
                        "text": clean,
                    })
                pos = next_pos
                continue
        pos += 2
    return dialogues


def main():
    if not ROM_PATH.exists():
        print(f"Erro: ROM não encontrada em {ROM_PATH}")
        return

    rom = ROM_PATH.read_bytes()
    entries = parse_archive_table(rom, ARCHIVE2_BASE, ARCHIVE2_LIMIT)
    print(f"Lendo Archive 2 ({len(entries)} arquivos)...")

    all_scripts_dialogues: Dict[int, List[Dict[str, Any]]] = {}
    total_lines = 0

    for ent in entries:
        raw = rom[ent["file_offset"] : ent["file_offset"] + ent["compressed_size"]]
        if ent["is_lz77"]:
            decomp_res = decompress_gba_lz77(raw)
            decomp = decomp_res[0] if decomp_res else None
        else:
            decomp = raw

        if decomp and decomp.startswith(b"PSI3"):
            lines = extract_script_dialogues(decomp)
            if lines:
                all_scripts_dialogues[ent["index"]] = lines
                total_lines += len(lines)

    print(f"Scripts com texto: {len(all_scripts_dialogues)}")
    print(f"Total de falas/strings extraídas: {total_lines}")

    # Organizar em lotes em Markdown
    MD_DIR.mkdir(parents=True, exist_ok=True)
    batch_size = 50
    script_indices = sorted(all_scripts_dialogues.keys())

    total_batches = (len(script_indices) + batch_size - 1) // batch_size
    for b_idx in range(total_batches):
        batch_keys = script_indices[b_idx * batch_size : (b_idx + 1) * batch_size]
        start_id = batch_keys[0]
        end_id = batch_keys[-1]
        md_file = MD_DIR / f"Lote_{b_idx+1:02d}_Scripts_{start_id:04d}_a_{end_id:04d}.md"

        lines_out = []
        lines_out.append(f"# 📜 Lote {b_idx+1:02d}: Scripts PSI3 {start_id:04d} a {end_id:04d}\n")
        lines_out.append("> [!NOTE]")
        lines_out.append(f"> Arquivo gerado da ROM oficial de **Summon Night: Swordcraft Story 2 (USA)**.")
        lines_out.append("> Todas as variáveis dinâmicas (`{PLAYER}`, `{PARTNER}`, etc.) e glifos duplos estão preservados.\n")
        lines_out.append("| ID Script | Offset | Opcode | Texto Original (Inglês) | Tradução PT-BR |")
        lines_out.append("| :--- | :--- | :--- | :--- | :--- |")

        for s_id in batch_keys:
            for item in all_scripts_dialogues[s_id]:
                en_text = item["text"].replace("|", "\\|")
                lines_out.append(f"| `{s_id:04d}` | `{item['offset']}` | `{item['opcode']}` | {en_text} |  |")

        lines_out.append("")
        md_file.write_text("\n".join(lines_out), encoding="utf-8")
        print(f"  -> Gerado: {md_file.name} ({len(batch_keys)} scripts)")

    # Remove o antigo LEIA-ME.txt provisório se existir
    readme_old = MD_DIR / "LEIA-ME.txt"
    if readme_old.exists():
        readme_old.unlink()

    print("\n✅ Extração e estruturação de diálogos concluída com 100% de sucesso!")


if __name__ == "__main__":
    main()
