"""Injetor de glifos minusculos acentuados PT-BR (áéíóúâêôãõçà) em fontes .NFTR."""
import struct
import sys
from pathlib import Path

LOWER_PTBR = [
    ("á", "a", "acute"),
    ("é", "e", "acute"),
    ("í", "i", "acute"),
    ("ó", "o", "acute"),
    ("ú", "u", "acute"),
    ("â", "a", "circ"),
    ("ê", "e", "circ"),
    ("ô", "o", "circ"),
    ("ã", "a", "tilde"),
    ("õ", "o", "tilde"),
    ("ç", "c", "cedilla"),
    ("à", "a", "grave"),
]


def _get_pixel(cell: bytes, width: int, bpp: int, x: int, y: int) -> int:
    bit_idx = (y * width + x) * bpp
    byte_idx = bit_idx // 8
    shift = 8 - bpp - (bit_idx % 8)
    mask = (1 << bpp) - 1
    return (cell[byte_idx] >> shift) & mask


def _set_pixel(cell: bytearray, width: int, bpp: int, x: int, y: int, val: int) -> None:
    bit_idx = (y * width + x) * bpp
    byte_idx = bit_idx // 8
    shift = 8 - bpp - (bit_idx % 8)
    mask = (1 << bpp) - 1
    cell[byte_idx] = (cell[byte_idx] & ~(mask << shift)) | ((val & mask) << shift)


def _draw_accent(cell: bytearray, cell_w: int, cell_h: int, bpp: int, glyph_w: int, accent: str) -> None:
    max_val = (1 << bpp) - 1
    cx = max(1, min(cell_w - 2, glyph_w // 2))
    if accent == "acute":
        pts = [(cx + 1, 0), (cx, 1)]
    elif accent == "grave":
        pts = [(cx - 1, 0), (cx, 1)]
    elif accent == "circ":
        pts = [(cx, 0), (cx - 1, 1), (cx + 1, 1)]
    elif accent == "tilde":
        pts = [(cx - 1, 1), (cx, 0), (cx + 1, 1), (cx + 2, 0)]
    elif accent == "cedilla":
        y_bot = min(cell_h - 1, cell_h - 2)
        pts = [(cx, y_bot), (cx, y_bot + 1), (cx - 1, y_bot + 1)]
    else:
        pts = []

    for x, y in pts:
        if 0 <= x < cell_w and 0 <= y < cell_h:
            _set_pixel(cell, cell_w, bpp, x, y, max_val)


def inject_ptbr_nftr(src_path: Path, dst_path: Path) -> None:
    data = bytearray(src_path.read_bytes())
    if data[:4] != b"RTFN":
        raise ValueError(f"{src_path.name}: header invalido")

    header_size, chunk_count = struct.unpack_from("<HH", data, 0x0C)
    offset = header_size

    plgc_off = hdwc_off = last_pamc_off = -1
    cmap: dict[int, int] = {}
    cell_w = cell_h = cell_size = bpp = 0
    glyph_count = 0

    for _ in range(chunk_count):
        magic = bytes(data[offset : offset + 4])
        size = struct.unpack_from("<I", data, offset + 4)[0]
        if magic == b"PLGC":
            plgc_off = offset
            cell_w, cell_h, cell_size = struct.unpack_from("<BBH", data, offset + 8)
            bpp = data[offset + 14]
            glyph_count = (size - 16) // cell_size
        elif magic == b"HDWC":
            hdwc_off = offset
        elif magic == b"PAMC":
            last_pamc_off = offset
            first_c, last_c, mtype, _ = struct.unpack_from("<HHII", data, offset + 8)
            body = offset + 20
            if mtype == 0:
                fg = struct.unpack_from("<H", data, body)[0]
                if fg != 0xFFFF:
                    for cp in range(first_c, last_c + 1):
                        cmap[cp] = fg + (cp - first_c)
            elif mtype == 1:
                for i in range(last_c - first_c + 1):
                    g = struct.unpack_from("<H", data, body + i * 2)[0]
                    if g != 0xFFFF:
                        cmap[first_c + i] = g
            elif mtype == 2:
                cnt = struct.unpack_from("<H", data, body)[0]
                for i in range(cnt):
                    cp, g = struct.unpack_from("<HH", data, body + 2 + i * 4)
                    if g != 0xFFFF:
                        cmap[cp] = g
        offset += size

    new_glyphs = bytearray()
    new_widths = bytearray()
    new_entries: list[tuple[int, int]] = []
    next_idx = glyph_count

    for idx, (target_ch, base_ch, accent) in enumerate(LOWER_PTBR):
        cp = 0xE040 + idx
        if cp in cmap:
            continue
        base_idx = cmap.get(ord(base_ch))
        if base_idx is None:
            continue
        g_off = plgc_off + 16 + base_idx * cell_size
        cell = bytearray(data[g_off : g_off + cell_size])
        w_off = hdwc_off + 16 + base_idx * 3
        left_b, gw_b, cw_b = struct.unpack_from("<bBB", data, w_off)
        _draw_accent(cell, cell_w, cell_h, bpp, gw_b, accent)
        new_glyphs.extend(cell)
        new_widths.extend(struct.pack("<bBB", left_b, gw_b, cw_b))
        new_entries.append((cp, next_idx))
        next_idx += 1

    # Reassemble chunks with appended glyphs, widths, and new PAMC scan chunk
    plgc_size = struct.unpack_from("<I", data, plgc_off + 4)[0]
    hdwc_size = struct.unpack_from("<I", data, hdwc_off + 4)[0]

    # Build new PAMC (type 2 = Scan)
    new_entries.sort(key=lambda x: x[0])
    pamc_body = bytearray(struct.pack("<H", len(new_entries)))
    for cp, gidx in new_entries:
        pamc_body.extend(struct.pack("<HH", cp, gidx))
    while len(pamc_body) % 4 != 0:
        pamc_body.append(0)
    pamc_size = 20 + len(pamc_body)
    pamc_chunk = (
        b"PAMC"
        + struct.pack("<IHHII", pamc_size, new_entries[0][0], new_entries[-1][0], 2, 0)
        + pamc_body
    )

    # Rebuild file cleanly
    out = bytearray(data[:header_size])
    offset = header_size
    for _ in range(chunk_count):
        magic = bytes(data[offset : offset + 4])
        size = struct.unpack_from("<I", data, offset + 4)[0]
        chunk = bytearray(data[offset : offset + size])
        if magic == b"PLGC":
            chunk.extend(new_glyphs)
            struct.pack_into("<I", chunk, 4, plgc_size + len(new_glyphs))
        elif magic == b"HDWC":
            chunk.extend(new_widths)
            struct.pack_into("<I", chunk, 4, hdwc_size + len(new_widths))
        elif offset == last_pamc_off:
            # Point last PAMC to the new PAMC chunk
            next_pamc_data_off = len(out) + len(chunk) + 8
            struct.pack_into("<I", chunk, 16, next_pamc_data_off)
        out.extend(chunk)
        offset += size

    out.extend(pamc_chunk)
    struct.pack_into("<I", out, 8, len(out))
    struct.pack_into("<H", out, 0x0E, chunk_count + 1)

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_bytes(out)
    print(f"{dst_path.name}: +{len(new_entries)} glifos PT-BR injetados ({len(out)} bytes)")


def main() -> int:
    base = Path(
        "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)"
    )
    src_dir = base / "extracted/nitrofs/data"
    dst_dir = base / "build/fonts"
    for name in ["trialFont10.NFTR", "trialFont12.NFTR"]:
        inject_ptbr_nftr(src_dir / name, dst_dir / name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
