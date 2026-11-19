#!/usr/bin/env python3
"""
OAM/NCER <-> PNG Compositor & Decompositor — Summon Night (NDS)
Parser direto de RECN (CEBK) + RGCN (CHAR) + RLCN (PLTT) sem depender de ndspy.ncer.
"""

import argparse
import struct
from pathlib import Path

OAM_SIZES = {
    (0, 0): (8, 8), (0, 1): (16, 16), (0, 2): (32, 32), (0, 3): (64, 64),
    (1, 0): (16, 8), (1, 1): (32, 8), (1, 2): (32, 16), (1, 3): (64, 32),
    (2, 0): (8, 16), (2, 1): (8, 32), (2, 2): (16, 32), (2, 3): (32, 64),
}


def parse_ncer(data: bytes):
    """Retorna (mapping_shift, cells) onde cada cell é lista de dicts OAM."""
    cebk_off = data.find(b"KBEC")
    if cebk_off == -1:
        raise ValueError("Bloco KBEC não encontrado no NCER")
    num_cells, bank_type, oam_off = struct.unpack_from("<HHI", data, cebk_off + 8)
    mapping_mode = struct.unpack_from("<I", data, cebk_off + 16)[0]
    mapping_shift = mapping_mode & 0x3

    entry_size = 16 if bank_type == 1 else 8
    cells_base = cebk_off + 8 + oam_off
    oams_base = cells_base + num_cells * entry_size

    cells = []
    for i in range(num_cells):
        e_off = cells_base + i * entry_size
        num_oams, _attr, first_oam_off = struct.unpack_from("<HHI", data, e_off)
        oam_list = []
        for j in range(num_oams):
            a0, a1, a2 = struct.unpack_from("<HHH", data, oams_base + first_oam_off + j * 6)
            y = a0 & 0xFF
            if y >= 128:
                y -= 256
            shape = (a0 >> 14) & 0x3
            x = a1 & 0x1FF
            if x >= 256:
                x -= 512
            h_flip = bool((a1 >> 12) & 1)
            v_flip = bool((a1 >> 13) & 1)
            size_idx = (a1 >> 14) & 0x3
            w, h = OAM_SIZES.get((shape, size_idx), (8, 8))
            tile = a2 & 0x3FF
            pal = (a2 >> 12) & 0xF
            oam_list.append({
                "x": x, "y": y, "w": w, "h": h,
                "h_flip": h_flip, "v_flip": v_flip,
                "tile": tile, "pal": pal,
            })
        cells.append(oam_list)
    return mapping_shift, cells


def parse_ncgr(data: bytes):
    char_off = data.find(b"RAHC")
    if char_off == -1:
        raise ValueError("Bloco RAHC não encontrado no NCGR")
    _h, _w, bpp_flag = struct.unpack_from("<HHI", data, char_off + 8)
    bpp = 8 if bpp_flag == 4 else 4
    px_size, px_off = struct.unpack_from("<II", data, char_off + 24)
    px_start = char_off + 8 + px_off
    return bpp, px_start, data[px_start : px_start + px_size]


def parse_nclr(data: bytes):
    pltt_off = data.find(b"TTLP")
    if pltt_off == -1:
        raise ValueError("Bloco TTLP não encontrado no NCLR")
    _bpp, _pad, pal_size, pal_off = struct.unpack_from("<IIII", data, pltt_off + 8)
    p_start = pltt_off + 8 + pal_off
    raw = data[p_start : p_start + pal_size]
    rgb = []
    for i in range(0, len(raw), 2):
        c = struct.unpack_from("<H", raw, i)[0]
        rgb.extend([(c & 0x1F) << 3, ((c >> 5) & 0x1F) << 3, ((c >> 10) & 0x1F) << 3])
    while len(rgb) < 256 * 3:
        rgb.extend([0, 0, 0])
    return rgb[: 256 * 3]


def extract_cells(narc_path: Path, out_dir: Path):
    from PIL import Image
    import ndspy.narc
    import ndspy.lz10
    raw = narc_path.read_bytes()
    if raw[:1] == b"\x10":
        raw = ndspy.lz10.decompress(raw)
    narc = ndspy.narc.NARC(raw)

    ncer_d = ncgr_d = nclr_d = None
    for f in narc.files:
        if f[:4] == b"RECN":
            ncer_d = f
        elif f[:4] == b"RGCN":
            ncgr_d = f
        elif f[:4] == b"RLCN":
            nclr_d = f

    if not (ncer_d and ncgr_d and nclr_d):
        raise ValueError(f"NARC incompleto: {narc_path.name}")

    mapping_shift, cells = parse_ncer(ncer_d)
    bpp, _, pixels = parse_ncgr(ncgr_d)
    pal_rgb = parse_nclr(nclr_d)

    px_indices = []
    if bpp == 4:
        for b in pixels:
            px_indices.append(b & 0x0F)
            px_indices.append((b >> 4) & 0x0F)
    else:
        px_indices = list(pixels)

    tile_step = 1 if bpp == 4 else 2
    out_dir.mkdir(parents=True, exist_ok=True)

    for c_idx, oams in enumerate(cells):
        if not oams:
            continue
        min_x = min(o["x"] for o in oams)
        min_y = min(o["y"] for o in oams)
        max_x = max(o["x"] + o["w"] for o in oams)
        max_y = max(o["y"] + o["h"] for o in oams)
        w, h = max(1, max_x - min_x), max(1, max_y - min_y)

        img = Image.new("P", (w, h), 0)
        img.putpalette(pal_rgb)
        img_px = img.load()

        for oam in reversed(oams):
            tw, th = oam["w"] // 8, oam["h"] // 8
            base_tile = oam["tile"] << mapping_shift
            for ty in range(th):
                for tx in range(tw):
                    tid = base_tile + (ty * tw + tx) * tile_step
                    tile = px_indices[tid * 64 : (tid + 1) * 64]
                    if len(tile) < 64:
                        continue
                    for py in range(8):
                        for px in range(8):
                            val = tile[py * 8 + px]
                            if val == 0:
                                continue
                            dx = (oam["w"] - 1 - (tx * 8 + px)) if oam["h_flip"] else (tx * 8 + px)
                            dy = (oam["h"] - 1 - (ty * 8 + py)) if oam["v_flip"] else (ty * 8 + py)
                            gx, gy = oam["x"] - min_x + dx, oam["y"] - min_y + dy
                            if 0 <= gx < w and 0 <= gy < h:
                                img_px[gx, gy] = val

        img.save(out_dir / f"cell_{c_idx:03d}.png")
    print(f"Extraídas {len(cells)} células OAM de {narc_path.name} para {out_dir}")


def pack_cells(narc_orig: Path, png_dir: Path, narc_out: Path):
    from PIL import Image
    import ndspy.narc
    import ndspy.lz10
    raw = narc_orig.read_bytes()
    is_lz10 = raw[:1] == b"\x10"
    if is_lz10:
        raw = ndspy.lz10.decompress(raw)
    narc = ndspy.narc.NARC(raw)

    ncer_d = ncgr_d = None
    ncgr_idx = None
    for idx, f in enumerate(narc.files):
        if f[:4] == b"RECN":
            ncer_d = f
        elif f[:4] == b"RGCN":
            ncgr_d = bytearray(f)
            ncgr_idx = idx

    if not (ncer_d and ncgr_d is not None):
        raise ValueError(f"NARC incompleto: {narc_orig.name}")

    mapping_shift, cells = parse_ncer(ncer_d)
    bpp, px_start, pixels = parse_ncgr(bytes(ncgr_d))

    px_indices = []
    if bpp == 4:
        for b in pixels:
            px_indices.append(b & 0x0F)
            px_indices.append((b >> 4) & 0x0F)
    else:
        px_indices = list(pixels)

    tile_step = 1 if bpp == 4 else 2
    written_tiles: set[int] = set()

    for c_idx, oams in enumerate(cells):
        png_path = png_dir / f"cell_{c_idx:03d}.png"
        if not oams or not png_path.exists():
            continue
        min_x = min(o["x"] for o in oams)
        min_y = min(o["y"] for o in oams)
        img = Image.open(png_path)
        w, h = img.size
        img_px = img.load()

        for oam in oams:
            tw, th = oam["w"] // 8, oam["h"] // 8
            base_tile = oam["tile"] << mapping_shift
            for ty in range(th):
                for tx in range(tw):
                    tid = base_tile + (ty * tw + tx) * tile_step
                    if tid in written_tiles or (tid + 1) * 64 > len(px_indices):
                        continue
                    written_tiles.add(tid)
                    for py in range(8):
                        for px in range(8):
                            dx = (oam["w"] - 1 - (tx * 8 + px)) if oam["h_flip"] else (tx * 8 + px)
                            dy = (oam["h"] - 1 - (ty * 8 + py)) if oam["v_flip"] else (ty * 8 + py)
                            gx, gy = oam["x"] - min_x + dx, oam["y"] - min_y + dy
                            if 0 <= gx < w and 0 <= gy < h:
                                px_indices[tid * 64 + py * 8 + px] = img_px[gx, gy]

    if bpp == 4:
        new_pixels = bytes((px_indices[i] & 0x0F) | ((px_indices[i + 1] & 0x0F) << 4) for i in range(0, len(px_indices), 2))
    else:
        new_pixels = bytes(px_indices)

    ncgr_d[px_start : px_start + len(new_pixels)] = new_pixels
    narc.files[ncgr_idx] = bytes(ncgr_d)

    out_bytes = narc.save()
    if is_lz10:
        out_bytes = ndspy.lz10.compress(out_bytes)
    narc_out.parent.mkdir(parents=True, exist_ok=True)
    narc_out.write_bytes(out_bytes)
    print(f"Empacotado: {narc_out.name} ({len(cells)} células OAM)")


def main():
    parser = argparse.ArgumentParser(description="Compositor OAM/NCER <-> PNG para NDS")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_ext = sub.add_parser("extract", help="Extrai células OAM para PNG")
    p_ext.add_argument("narc", type=Path)
    p_ext.add_argument("-o", "--output", type=Path, required=True)

    p_pack = sub.add_parser("pack", help="Empacota PNGs de volta no NARC")
    p_pack.add_argument("narc_orig", type=Path)
    p_pack.add_argument("png_dir", type=Path)
    p_pack.add_argument("-o", "--output", type=Path, required=True)

    args = parser.parse_args()
    if args.cmd == "extract":
        extract_cells(args.narc, args.output)
    elif args.cmd == "pack":
        pack_cells(args.narc_orig, args.png_dir, args.output)


if __name__ == "__main__":
    main()
