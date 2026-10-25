#!/usr/bin/env python3
"""
Injetor de Fonte Acentuada PT-BR (`BIT\0` @ 0x08944D3C + Tabela SJIS @ 0x084C37D4)
Summon Night: Swordcraft Story 2 (USA) [BSKE]
===================================================================================
1. Lê os glifos originais de 'a, c, e, i, o, u' e 'A, C, E, I, O, U' na fonte BIT\0
   (1bpp, 12x12 pixels = 24 bytes por glifo, base @ 0x08944D3C + 0x1C = 0x08944D58).
2. Constrói os 24 caracteres acentuados do Português (PT-BR):
     Minúsculas: á, à, â, ã, é, ê, í, ó, ô, õ, ú, ç
     Maiúsculas: Á, À, Â, Ã, É, Ê, Í, Ó, Ô, Õ, Ú, Ç
3. Grava os 24 novos bitmaps nos slots livres (357..380) no final de BIT\0.
4. Registra os códigos Shift-JIS (0x8440..0x8457) na tabela SJIS oficial da ROM (0x084C37D4).
"""

import struct
from pathlib import Path
from typing import Dict, List, Tuple

GBA_ROM_BASE = 0x08000000
SJIS_TABLE_ADDR = 0x084C37D4
BIT0_ARCHIVE_ADDR = 0x08944D3C
BIT0_GLYPH_BASE_ADDR = BIT0_ARCHIVE_ADDR + 0x1C  # 0x08944D58

# 24 caracteres acentuados do PT-BR mapeados para os códigos Shift-JIS 0x8440..0x8457
# e alocados nos slots livres 357..380 do BIT\0 do SN2
PTBR_ACCENT_SPECS: List[Tuple[str, int, int, str, str]] = [
    # (char, sjis_be, target_glyph_id, base_char, accent_type)
    ("á", 0x8440, 357, "a", "acute"),
    ("à", 0x8441, 358, "a", "grave"),
    ("â", 0x8442, 359, "a", "circumflex"),
    ("ã", 0x8443, 360, "a", "tilde"),
    ("é", 0x8444, 361, "e", "acute"),
    ("ê", 0x8445, 362, "e", "circumflex"),
    ("í", 0x8446, 363, "i", "acute"),
    ("ó", 0x8447, 364, "o", "acute"),
    ("ô", 0x8448, 365, "o", "circumflex"),
    ("õ", 0x8449, 366, "o", "tilde"),
    ("ú", 0x844A, 367, "u", "acute"),
    ("ç", 0x844B, 368, "c", "cedilla"),
    ("Á", 0x844C, 369, "A", "acute_upper"),
    ("À", 0x844D, 370, "A", "grave_upper"),
    ("Â", 0x844E, 371, "A", "circumflex_upper"),
    ("Ã", 0x844F, 372, "A", "tilde_upper"),
    ("É", 0x8450, 373, "E", "acute_upper"),
    ("Ê", 0x8451, 374, "E", "circumflex_upper"),
    ("Í", 0x8452, 375, "I", "acute_upper"),
    ("Ó", 0x8453, 376, "O", "acute_upper"),
    ("Ô", 0x8454, 377, "O", "circumflex_upper"),
    ("Õ", 0x8455, 378, "O", "tilde_upper"),
    ("Ú", 0x8456, 379, "U", "acute_upper"),
    ("Ç", 0x8457, 380, "C", "cedilla_upper"),
]

PTBR_CHAR_TO_SJIS: Dict[str, int] = {ch: sjis for ch, sjis, _, _, _ in PTBR_ACCENT_SPECS}
PTBR_SJIS_TO_CHAR: Dict[int, str] = {sjis: ch for ch, sjis, _, _, _ in PTBR_ACCENT_SPECS}

# Glyph IDs das letras base no BIT\0 do SN2
BASE_CHAR_GLYPH_ID: Dict[str, int] = {
    "a": 112,
    "c": 114,
    "e": 116,
    "i": 120,
    "o": 126,
    "u": 132,
    "A": 86,
    "C": 88,
    "E": 90,
    "I": 94,
    "O": 100,
    "U": 106,
}


def str_to_row12(pattern: str) -> int:
    val = 0
    for x, c in enumerate(pattern[:12]):
        if c == "#":
            val |= 1 << (11 - x)
    return val


def sjis_to_table_index(sjis_be: int) -> int:
    b0 = (sjis_be >> 8) & 0xFF
    b1 = sjis_be & 0xFF
    return (b0 - 0x81) * 192 + (b1 - 0x40)


def read_glyph_rows(rom: bytes, glyph_id: int) -> List[int]:
    off = (BIT0_GLYPH_BASE_ADDR - GBA_ROM_BASE) + (glyph_id - 1) * 24
    rows = []
    for r in range(12):
        b0 = rom[off + r * 2]
        b1 = rom[off + r * 2 + 1]
        rows.append((b0 << 4) | (b1 >> 4))
    return rows


def encode_glyph_rows(rows: List[int]) -> bytes:
    out = bytearray(24)
    for r in range(12):
        row12 = rows[r] & 0xFFF
        out[r * 2] = (row12 >> 4) & 0xFF
        out[r * 2 + 1] = (row12 & 0xF) << 4
    return bytes(out)


def build_accented_glyph(base_rows: List[int], base_char: str, accent_type: str) -> List[int]:
    rows = list(base_rows)

    # 1. Minúsculas (a, e, o, u começam na linha 4; i tem ponto nas linhas 1..2)
    if accent_type == "acute":
        if base_char == "i":
            rows[0] = str_to_row12("...#........")
            rows[1] = str_to_row12("..#.........")
            rows[2] = str_to_row12("............")
        else:
            rows[1] = str_to_row12("...#........")
            rows[2] = str_to_row12("..#.........")
    elif accent_type == "grave":
        rows[1] = str_to_row12(".#..........")
        rows[2] = str_to_row12("..#.........")
    elif accent_type == "circumflex":
        rows[1] = str_to_row12("..#.........")
        rows[2] = str_to_row12(".#.#........")
    elif accent_type == "tilde":
        rows[1] = str_to_row12(".##.#.......")
        rows[2] = str_to_row12("#..#........")
    elif accent_type == "cedilla":
        rows[10] = str_to_row12("..#.........")
        rows[11] = str_to_row12(".##.........")

    # 2. Maiúsculas (compacta topo nas linhas 3..9 para liberar linhas 0..1 para acento)
    elif accent_type.endswith("_upper"):
        if accent_type == "cedilla_upper":
            rows[10] = str_to_row12("..#.........")
            rows[11] = str_to_row12(".##.........")
            return rows

        if base_char == "A":
            rows[2] = str_to_row12("............")
            rows[3] = str_to_row12("..#.........")
            rows[4] = str_to_row12(".#.#........")
            rows[5] = str_to_row12("#...#.......")
            rows[6] = str_to_row12("#####.......")
            rows[7] = str_to_row12("#...#.......")
            rows[8] = str_to_row12("#...#.......")
            rows[9] = str_to_row12("#...#.......")
        elif base_char == "E":
            rows[2] = str_to_row12("............")
            rows[3] = str_to_row12("#####.......")
            rows[4] = str_to_row12("#...........")
            rows[5] = str_to_row12("#...........")
            rows[6] = str_to_row12("####........")
            rows[7] = str_to_row12("#...........")
            rows[8] = str_to_row12("#...........")
            rows[9] = str_to_row12("#####.......")
        elif base_char == "I":
            rows[2] = str_to_row12("............")
            rows[3] = str_to_row12(".###........")
            rows[4] = str_to_row12("..#.........")
            rows[5] = str_to_row12("..#.........")
            rows[6] = str_to_row12("..#.........")
            rows[7] = str_to_row12("..#.........")
            rows[8] = str_to_row12("..#.........")
            rows[9] = str_to_row12(".###........")
        elif base_char == "O":
            rows[2] = str_to_row12("............")
            rows[3] = str_to_row12(".###........")
            rows[4] = str_to_row12("#...#.......")
            rows[5] = str_to_row12("#...#.......")
            rows[6] = str_to_row12("#...#.......")
            rows[7] = str_to_row12("#...#.......")
            rows[8] = str_to_row12("#...#.......")
            rows[9] = str_to_row12(".###........")
        elif base_char == "U":
            rows[2] = str_to_row12("............")
            rows[3] = str_to_row12("#...#.......")
            rows[4] = str_to_row12("#...#.......")
            rows[5] = str_to_row12("#...#.......")
            rows[6] = str_to_row12("#...#.......")
            rows[7] = str_to_row12("#...#.......")
            rows[8] = str_to_row12("#...#.......")
            rows[9] = str_to_row12(".###........")

        if "acute" in accent_type:
            rows[0] = str_to_row12("...#........")
            rows[1] = str_to_row12("..#.........")
        elif "grave" in accent_type:
            rows[0] = str_to_row12(".#..........")
            rows[1] = str_to_row12("..#.........")
        elif "circumflex" in accent_type:
            rows[0] = str_to_row12("..#.........")
            rows[1] = str_to_row12(".#.#........")
        elif "tilde" in accent_type:
            rows[0] = str_to_row12(".##.#.......")
            rows[1] = str_to_row12("#..#........")

    return rows


def inject_ptbr_font_into_rom(rom_bytes: bytes) -> bytes:
    """
    Injeta os 24 glifos acentuados PT-BR na fonte BIT\\0 (0x08944D58)
    e atualiza a tabela Shift-JIS da ROM (0x084C37D4).
    """
    rom = bytearray(rom_bytes)

    # 1. Carrega os bitmaps base originais
    base_rows_cache = {}
    for ch, gid in BASE_CHAR_GLYPH_ID.items():
        base_rows_cache[ch] = read_glyph_rows(rom, gid)

    # 2. Constrói e grava cada caractere acentuado
    for char, sjis_be, target_gid, base_char, accent_type in PTBR_ACCENT_SPECS:
        base_rows = base_rows_cache[base_char]
        accent_rows = build_accented_glyph(base_rows, base_char, accent_type)
        glyph_bytes = encode_glyph_rows(accent_rows)

        # Grava no BIT\0
        glyph_off = (BIT0_GLYPH_BASE_ADDR - GBA_ROM_BASE) + (target_gid - 1) * 24
        rom[glyph_off : glyph_off + 24] = glyph_bytes

        # Atualiza a tabela Shift-JIS da ROM
        sjis_idx = sjis_to_table_index(sjis_be)
        tbl_off = (SJIS_TABLE_ADDR - GBA_ROM_BASE) + sjis_idx * 2
        struct.pack_into("<H", rom, tbl_off, target_gid)

    return bytes(rom)


if __name__ == "__main__":
    from build_ptbr_rom import ORIGINAL_ROM
    rom_bytes = ORIGINAL_ROM.read_bytes()
    mod_bytes = inject_ptbr_font_into_rom(rom_bytes)
    print("Sucesso! 24 glifos acentuados PT-BR injetados em BIT\\0 e registrados na tabela 0x084C37D4.")
