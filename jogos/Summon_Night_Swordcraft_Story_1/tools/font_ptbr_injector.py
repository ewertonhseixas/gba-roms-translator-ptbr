#!/usr/bin/env python3
"""
Injetor de Fonte Acenctuada PT-BR (`BIT\0` @ 0x087077EC + Tabela SJIS @ 0x081DB270)
Summon Night: Swordcraft Story (USA) [AB4E]
===================================================================================
1. Lê os glifos originais de 'a, e, i, o, u, c' e 'A, E, I, O, U, C' na fonte BIT\0
   (1bpp, 12x12 pixels = 24 bytes por glifo, base @ 0x087077EC + 0x1C).
2. Gera os 24 caracteres acentuados do Português (PT-BR):
     Minúsculas: á, à, â, ã, é, ê, í, ó, ô, õ, ú, ç
     Maiúsculas: Á, À, Â, Ã, É, Ê, Í, Ó, Ô, Õ, Ú, Ç
   O motor do jogo (`0x080074CC`) aplica sombra de 1px à direita e abaixo em tempo real!
3. Aloca os 24 glifos nos slots livres do final de `BIT\0` (1666..1680) e em 9 slots de
   Kanji não utilizados pela ROM americana (1625..1633), mapeando-os nos códigos
   Shift-JIS livres `0x8440..0x8457` na tabela `0x081DB270`.
"""

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.stdout.reconfigure(encoding="utf-8")

GBA_ROM_BASE = 0x08000000
SJIS_TABLE_ADDR = 0x081DB270
BIT0_ARCHIVE_ADDR = 0x087077EC
BIT0_GLYPH_BASE_ADDR = BIT0_ARCHIVE_ADDR + 0x1C  # 0x08707808

# Mapeamento oficial dos 24 caracteres PT-BR para códigos Shift-JIS livres (0x8440..0x8457)
# e seus glyphIds dedicados em BIT\0 (1666..1680 + 1625..1633)
PTBR_ACCENT_SPECS: List[Tuple[str, int, int, str, str]] = [
    # (char, sjis_be, target_glyph_id, base_char, accent_type)
    ("á", 0x8440, 1666, "a", "acute"),
    ("à", 0x8441, 1667, "a", "grave"),
    ("â", 0x8442, 1668, "a", "circumflex"),
    ("ã", 0x8443, 1669, "a", "tilde"),
    ("é", 0x8444, 1670, "e", "acute"),
    ("ê", 0x8445, 1671, "e", "circumflex"),
    ("í", 0x8446, 1672, "i", "acute"),
    ("ó", 0x8447, 1673, "o", "acute"),
    ("ô", 0x8448, 1674, "o", "circumflex"),
    ("õ", 0x8449, 1675, "o", "tilde"),
    ("ú", 0x844A, 1676, "u", "acute"),
    ("ç", 0x844B, 1677, "c", "cedilla"),
    ("Á", 0x844C, 1678, "A", "acute_upper"),
    ("À", 0x844D, 1679, "A", "grave_upper"),
    ("Â", 0x844E, 1680, "A", "circumflex_upper"),
    ("Ã", 0x844F, 1625, "A", "tilde_upper"),
    ("É", 0x8450, 1626, "E", "acute_upper"),
    ("Ê", 0x8451, 1627, "E", "circumflex_upper"),
    ("Í", 0x8452, 1628, "I", "acute_upper"),
    ("Ó", 0x8453, 1629, "O", "acute_upper"),
    ("Ô", 0x8454, 1630, "O", "circumflex_upper"),
    ("Õ", 0x8455, 1631, "O", "tilde_upper"),
    ("Ú", 0x8456, 1632, "U", "acute_upper"),
    ("Ç", 0x8457, 1633, "C", "cedilla_upper"),
    ("º", 0x8458, 1634, "o", "ordinal_o"),
    ("ª", 0x8459, 1635, "a", "ordinal_a"),
]

PTBR_CHAR_TO_SJIS: Dict[str, int] = {ch: sjis for ch, sjis, _, _, _ in PTBR_ACCENT_SPECS}
PTBR_SJIS_TO_CHAR: Dict[int, str] = {sjis: ch for ch, sjis, _, _, _ in PTBR_ACCENT_SPECS}

BASE_CHAR_SJIS: Dict[str, int] = {
    "A": 0x8260, "C": 0x8262, "E": 0x8264, "I": 0x8268, "O": 0x826E, "U": 0x8274,
    "a": 0x8281, "c": 0x8283, "e": 0x8285, "i": 0x8289, "o": 0x828F, "u": 0x8295,
}


def str_to_row12(pattern: str) -> int:
    """Converte string de 12 chars ('#' ou '.') para inteiro de 12 bits."""
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
    """
    Constrói o bitmap 12x12 de um caractere acentuado a partir do glifo base original.
    """
    rows = list(base_rows)

    # 1. Minúsculas (a, e, o, u ocupam linhas 4..9; 'i' tem pingo nas linhas 1..2)
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
        # 'c' ocupa linhas 4..9; cedilha vai nas linhas 10..11
        rows[10] = str_to_row12("..#.........")
        rows[11] = str_to_row12(".##.........")
    elif accent_type == "ordinal_o":
        rows = [0] * 12
        rows[1] = str_to_row12(".##.........")
        rows[2] = str_to_row12("#..#........")
        rows[3] = str_to_row12("#..#........")
        rows[4] = str_to_row12(".##.........")
        rows[6] = str_to_row12("####........")
    elif accent_type == "ordinal_a":
        rows = [0] * 12
        rows[1] = str_to_row12(".###........")
        rows[2] = str_to_row12("#..#........")
        rows[3] = str_to_row12("#..#........")
        rows[4] = str_to_row12(".###........")
        rows[6] = str_to_row12("####........")

    # 2. Maiúsculas (A, E, I, O, U ocupam linhas 1..9; compactamos o topo para linhas 3..9
    #    para deixar as linhas 0..1 livres para o acento sem colidir!)
    elif accent_type.endswith("_upper"):
        if accent_type == "cedilla_upper":
            # 'C' ocupa linhas 1..9; cedilha vai nas linhas 10..11
            rows[10] = str_to_row12("..#.........")
            rows[11] = str_to_row12(".##.........")
            return rows

        # Compacta o corpo da letra maiúscula em 2px no topo (linhas 3..9 em vez de 1..9)
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

        # Desenha o acento nas linhas 0..1
        if accent_type == "acute_upper":
            rows[0] = str_to_row12("...#........")
            rows[1] = str_to_row12("..#.........")
        elif accent_type == "grave_upper":
            rows[0] = str_to_row12(".#..........")
            rows[1] = str_to_row12("..#.........")
        elif accent_type == "circumflex_upper":
            rows[0] = str_to_row12("..#.........")
            rows[1] = str_to_row12(".#.#........")
        elif accent_type == "tilde_upper":
            rows[0] = str_to_row12(".##.#.......")
            rows[1] = str_to_row12("#..#........")

    return rows


def inject_ptbr_font_into_rom(rom_bytes: bytes) -> bytes:
    """
    Injeta os 24 glifos acentuados PT-BR diretamente em `BIT\0` (`0x08707808`)
    e registra seus códigos Shift-JIS (`0x8440..0x8457`) na tabela `0x081DB270`.
    """
    rom_mut = bytearray(rom_bytes)
    tbl_off = SJIS_TABLE_ADDR - GBA_ROM_BASE
    glyph_base_off = BIT0_GLYPH_BASE_ADDR - GBA_ROM_BASE

    # Carrega os glifos base originais
    base_glyphs: Dict[str, List[int]] = {}
    for b_ch, b_sjis in BASE_CHAR_SJIS.items():
        t_idx = sjis_to_table_index(b_sjis)
        gid = struct.unpack_from("<H", rom_bytes, tbl_off + t_idx * 2)[0]
        base_glyphs[b_ch] = read_glyph_rows(rom_bytes, gid)

    for ch, sjis_be, target_gid, base_ch, acc_type in PTBR_ACCENT_SPECS:
        new_rows = build_accented_glyph(base_glyphs[base_ch], base_ch, acc_type)
        glyph_bytes = encode_glyph_rows(new_rows)

        # Grava os 24 bytes do glifo em BIT\0
        g_off = glyph_base_off + (target_gid - 1) * 24
        rom_mut[g_off : g_off + 24] = glyph_bytes

        # Atualiza a tabela Shift-JIS -> glyphId em 0x081DB270
        t_idx = sjis_to_table_index(sjis_be)
        struct.pack_into("<H", rom_mut, tbl_off + t_idx * 2, target_gid)

    return bytes(rom_mut)


def main():
    rom_path = Path("rom/Summon Night - Swordcraft Story (USA).gba")
    rom = rom_path.read_bytes()
    patched = inject_ptbr_font_into_rom(rom)

    print("=" * 80)
    print(" GLIFOS ACENTUADOS PT-BR (12x12 1BPP) INJETADOS EM BIT\\0 (0x08707808)")
    print("=" * 80)

    # Mostra uma amostra dos glifos gerados para inspeção visual
    for ch, sjis_be, target_gid, _, _ in PTBR_ACCENT_SPECS:
        if ch in ("á", "ã", "é", "ê", "í", "ó", "ç", "Á", "Ã", "É", "Ç"):
            rows = read_glyph_rows(patched, target_gid)
            print(f"\n[{ch}] SJIS=0x{sjis_be:04X} -> glyphId={target_gid}:")
            for r, bits in enumerate(rows):
                line = "".join("#" if (bits & (1 << (11 - x))) else "." for x in range(12))
                print(f"  {r:2d}: {line}")


if __name__ == "__main__":
    main()
