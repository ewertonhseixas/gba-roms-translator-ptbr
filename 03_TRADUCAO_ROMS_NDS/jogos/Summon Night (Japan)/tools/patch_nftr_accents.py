#!/usr/bin/env python3
"""
NFTR PT-BR Accent Patcher — Summon Night (NDS)
Adiciona os 24 glifos acentuados do Português Brasileiro (cp1252: 0xC0-0xFF)
em font12jp.NFTR (12x12, 2bpp) copiando os glifos ASCII base e desenhando
os diacríticos, salvando em build/font12jp_ptbr.NFTR.
"""

import argparse
import struct
from pathlib import Path

# Mapeamento: (char, sjis_code, base_ascii, accent_type)
# 24 códigos Shift-JIS já existentes no PAMC (0x88A2..0x88D4) de font12jp.NFTR
PTBR_ACCENTS = [
    ("À", 0x88A2, "A", "grave"),
    ("Á", 0x88A3, "A", "acute"),
    ("Â", 0x88A4, "A", "circ"),
    ("Ã", 0x88A5, "A", "tilde"),
    ("Ç", 0x88AB, "C", "cedilla"),
    ("É", 0x88AC, "E", "acute"),
    ("Ê", 0x88B3, "E", "circ"),
    ("Í", 0x88B5, "I", "acute"),
    ("Ó", 0x88B6, "O", "acute"),
    ("Ô", 0x88BB, "O", "circ"),
    ("Õ", 0x88C0, "O", "tilde"),
    ("Ú", 0x88C3, "U", "acute"),
    ("à", 0x88C4, "a", "grave"),
    ("á", 0x88C5, "a", "acute"),
    ("â", 0x88C8, "a", "circ"),
    ("ã", 0x88C9, "a", "tilde"),
    ("ç", 0x88CA, "c", "cedilla"),
    ("é", 0x88CB, "e", "acute"),
    ("ê", 0x88CC, "e", "circ"),
    ("í", 0x88CD, "i", "acute"),
    ("ó", 0x88CF, "o", "acute"),
    ("ô", 0x88D0, "o", "circ"),
    ("õ", 0x88D3, "o", "tilde"),
    ("ú", 0x88D4, "u", "acute"),
]


def decode_glyph_12x12_2bpp(gdata: bytes) -> list[list[int]]:
    grid = []
    for y in range(12):
        bits = int.from_bytes(gdata[y * 3 : y * 3 + 3], "big")
        row = [(bits >> (22 - x * 2)) & 3 for x in range(12)]
        grid.append(row)
    return grid


def encode_glyph_12x12_2bpp(grid: list[list[int]]) -> bytes:
    out = bytearray()
    for y in range(12):
        bits = 0
        for x in range(12):
            bits |= (grid[y][x] & 3) << (22 - x * 2)
        out.extend(bits.to_bytes(3, "big"))
    return bytes(out)


def draw_accent(grid: list[list[int]], width: int, base_char: str, accent: str) -> list[list[int]]:
    g = [row[:] for row in grid]
    cx = max(2, min(9, width // 2))

    if accent == "cedilla":
        # Desenha cedilha em y=10..11 abaixo do c/C
        if cx < 11:
            g[10][cx] = 3
            g[11][cx] = 3
            if cx > 0:
                g[11][cx - 1] = 2
        return g

    is_upper = base_char.isupper()
    if is_upper:
        # Desloca a maiúscula 1 pixel para baixo para dar espaço ao acento em y=0..1
        g = [[0] * 12] + g[:11]
        y0 = 0
    else:
        if base_char == "i":
            # Remove o pingo do 'i' nas linhas 0..3
            for y in range(4):
                for x in range(12):
                    g[y][x] = 0
        y0 = 0

    if accent == "acute":
        g[y0][min(11, cx + 1)] = 3
        g[y0 + 1][cx] = 3
    elif accent == "grave":
        g[y0][max(0, cx - 1)] = 3
        g[y0 + 1][cx] = 3
    elif accent == "circ":
        g[y0][cx] = 3
        g[y0 + 1][max(0, cx - 1)] = 3
        g[y0 + 1][min(11, cx + 1)] = 3
    elif accent == "tilde":
        g[y0][max(0, cx - 1)] = 3
        g[y0][cx] = 2
        g[y0 + 1][cx] = 3
        g[y0 + 1][min(11, cx + 1)] = 3

    return g


def patch_nftr(nftr_in: Path, nftr_out: Path):
    data = nftr_in.read_bytes()
    magic, bom, ver, total_size, h_size, num_blocks = struct.unpack_from("<4sHHIHH", data, 0)
    if magic != b"RTFN":
        raise ValueError(f"Arquivo inválido (esperado RTFN, obtido {magic})")

    blocks = []
    off = h_size
    for _ in range(num_blocks):
        b_magic, b_size = struct.unpack_from("<4sI", data, off)
        blocks.append([b_magic, bytearray(data[off : off + b_size])])
        off += b_size

    # Encontra blocos principais
    fnif_idx = next(i for i, b in enumerate(blocks) if b[0] == b"FNIF")
    plgc_idx = next(i for i, b in enumerate(blocks) if b[0] == b"PLGC")
    hdwc_idx = next(i for i, b in enumerate(blocks) if b[0] == b"HDWC")
    pamc_indices = [i for i, b in enumerate(blocks) if b[0] == b"PAMC"]

    # Descobre índice inicial do ASCII (0x0020..0x007E, type=0)
    ascii_start_glyph = 0
    for idx in pamc_indices:
        c_first, c_last, c_type, _ = struct.unpack_from("<HHII", blocks[idx][1], 8)
        if c_first == 0x0020 and c_type == 0:
            ascii_start_glyph = struct.unpack_from("<H", blocks[idx][1], 20)[0]
            break

    plgc_buf = blocks[plgc_idx][1]
    cw, ch, clen, baseline, maxw, bpp, rot = struct.unpack_from("<BBHBBBB", plgc_buf, 8)
    orig_glyphs = (len(plgc_buf) - 16) // clen

    hdwc_buf = blocks[hdwc_idx][1]

    # Mapeia cada código Shift-JIS existente nos blocos PAMC para seu glyph_id
    def find_glyph_id(code: int) -> int:
        for idx in pamc_indices:
            p_buf = blocks[idx][1]
            c_first, c_last, c_type, _ = struct.unpack_from("<HHII", p_buf, 8)
            if c_first <= code <= c_last:
                if c_type == 0:
                    start_g = struct.unpack_from("<H", p_buf, 20)[0]
                    return start_g + (code - c_first)
                elif c_type == 1:
                    gid = struct.unpack_from("<H", p_buf, 20 + (code - c_first) * 2)[0]
                    if gid != 0xFFFF:
                        return gid
                elif c_type == 2:
                    cnt = struct.unpack_from("<H", p_buf, 20)[0]
                    for i in range(cnt):
                        c_val, gid = struct.unpack_from("<HH", p_buf, 22 + i * 4)
                        if c_val == code:
                            return gid
        raise ValueError(f"Código Shift-JIS 0x{code:04X} não encontrado no PAMC!")

    replaced_count = 0
    for ch_str, cp_code, base_ascii, accent in PTBR_ACCENTS:
        base_id = ascii_start_glyph + (ord(base_ascii) - 0x0020)
        base_gdata = bytes(plgc_buf[16 + base_id * clen : 16 + (base_id + 1) * clen])
        l, w, a = struct.unpack_from("<bBB", hdwc_buf, 16 + base_id * 3)

        grid = decode_glyph_12x12_2bpp(base_gdata)
        patched_grid = draw_accent(grid, w, base_ascii, accent)

        target_gid = find_glyph_id(cp_code)
        plgc_buf[16 + target_gid * clen : 16 + (target_gid + 1) * clen] = encode_glyph_12x12_2bpp(patched_grid)
        struct.pack_into("<bBB", hdwc_buf, 16 + target_gid * 3, l, w, a)
        replaced_count += 1

    # Monta arquivo final (estrutura e tamanhos dos blocos preservados)
    out_bytes = bytearray(data[:h_size])
    for _, b_data in blocks:
        out_bytes.extend(b_data)

    nftr_out.parent.mkdir(parents=True, exist_ok=True)
    nftr_out.write_bytes(bytes(out_bytes))
    print(f"NFTR PT-BR gerada: {nftr_out} ({replaced_count} glifos sobrescritos in-place, {len(out_bytes)} bytes)")


def main():
    base = Path("03_TRADUCAO_ROMS_NDS/jogos/Summon Night (Japan)")
    parser = argparse.ArgumentParser(description="Adiciona acentos PT-BR em font12jp.NFTR")
    parser.add_argument("--input", type=Path, default=base / "extracted" / "nitrofs" / "font12jp.NFTR")
    parser.add_argument("--output", type=Path, default=base / "build" / "font12jp_ptbr.NFTR")
    args = parser.parse_args()
    patch_nftr(args.input, args.output)


if __name__ == "__main__":
    main()
