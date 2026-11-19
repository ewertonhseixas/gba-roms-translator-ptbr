#!/usr/bin/env python3
"""
UI Graphics Tool — Summon Night (NDS)
Converte gráficos Nitro (.NCGR/.NCBR + .NCLR + .NSCR) para PNG paletizado (mode='P')
e reconverte PNGs editados de volta para .NCGR/.NCBR, empacotando em .narc com compressão LZ10.
"""

import argparse
import os
import struct
from pathlib import Path
from PIL import Image
import ndspy.narc
import ndspy.lz10

TARGETS = [
    "charaselect/sn0_cs_sub_title.narc",
    "charaselect/sn0_cs_main_bot.narc",
    "charaselect/sn0_cs_sub_pane00.narc",
    "charaselect/sn0_cs_sub_pane01.narc",
    "charaselect/sn0_cs_sub_pane02.narc",
    "charaselect/sn0_cs_sub_pane03.narc",
    "input/input_bg_main0000.narc",
    "input/input_sp_main0000.narc",
    "input/input_sp_main0001.narc",
]


def parse_nclr(data: bytes) -> list[tuple[int, int, int]]:
    """Lê a paleta RGB888 de um arquivo NCLR (RLCN)."""
    # Header RLCN: 16 bytes, depois bloco TTLP
    ttlp_idx = data.find(b"TTLP")
    if ttlp_idx == -1:
        ttlp_idx = data.find(b"PLTT")
    if ttlp_idx == -1:
        raise ValueError("Bloco TTLP/PLTT não encontrado no NCLR")
    # TTLP: magic(4), size(4), bpp_flag(4), unk(4), pal_size(4), colors_offset(4)
    # Cores começam em ttlp_idx + 24
    pal_data_offset = ttlp_idx + 24
    colors = []
    for i in range(pal_data_offset, len(data) - 1, 2):
        bgr555 = struct.unpack_from("<H", data, i)[0]
        r = (bgr555 & 0x1F) << 3
        g = ((bgr555 >> 5) & 0x1F) << 3
        b = ((bgr555 >> 10) & 0x1F) << 3
        colors.append((r, g, b))
    return colors


def parse_ncgr(data: bytes) -> dict:
    """Lê um arquivo NCGR/NCBR (RGCN) e retorna metadados + pixel data."""
    char_idx = data.find(b"RAHC")
    if char_idx == -1:
        char_idx = data.find(b"CHAR")
    if char_idx == -1:
        raise ValueError("Bloco RAHC/CHAR não encontrado no NCGR/NCBR")
    # CHAR: magic(4), size(4), tiles_y(2), tiles_x(2), bpp_flag(4), unk1(4), unk2(4), data_size(4), data_offset(4)
    tiles_y, tiles_x = struct.unpack_from("<HH", data, char_idx + 8)
    bpp_flag = struct.unpack_from("<I", data, char_idx + 12)[0]
    is_8bpp = (bpp_flag == 4)
    data_size = struct.unpack_from("<I", data, char_idx + 24)[0]
    data_offset = struct.unpack_from("<I", data, char_idx + 28)[0]
    pixel_start = char_idx + 8 + data_offset
    pixel_bytes = data[pixel_start : pixel_start + data_size]

    # Se tiles_x == 0xFFFF ou tiles_y == 0xFFFF (comum em sprites 1D), calcula baseado no tamanho
    num_tiles = data_size // (64 if is_8bpp else 32)
    if tiles_x == 0xFFFF or tiles_y == 0xFFFF:
        tiles_x = 16 if num_tiles >= 16 else num_tiles
        tiles_y = (num_tiles + tiles_x - 1) // tiles_x

    return {
        "tiles_x": tiles_x,
        "tiles_y": tiles_y,
        "is_8bpp": is_8bpp,
        "pixel_bytes": pixel_bytes,
        "char_idx": char_idx,
        "pixel_start": pixel_start,
        "data_size": data_size,
    }


def decode_tiles(pixel_bytes: bytes, tiles_x: int, tiles_y: int, is_8bpp: bool) -> Image.Image:
    """Decodifica tiles 8x8 (4bpp ou 8bpp) para uma imagem PIL mode='P'."""
    w = tiles_x * 8
    h = tiles_y * 8
    img = Image.new("P", (w, h), 0)
    pixels = img.load()

    tile_size = 64 if is_8bpp else 32
    num_tiles = len(pixel_bytes) // tile_size

    for t in range(min(num_tiles, tiles_x * tiles_y)):
        tx = t % tiles_x
        ty = t // tiles_x
        base = t * tile_size
        for py in range(8):
            for px in range(8):
                if is_8bpp:
                    idx = pixel_bytes[base + py * 8 + px]
                else:
                    b = pixel_bytes[base + py * 4 + (px // 2)]
                    idx = (b & 0x0F) if (px % 2 == 0) else (b >> 4)
                pixels[tx * 8 + px, ty * 8 + py] = idx
    return img


def encode_tiles(img: Image.Image, tiles_x: int, tiles_y: int, is_8bpp: bool, orig_size: int) -> bytes:
    """Codifica uma imagem PIL mode='P' de volta para tiles 8x8 (4bpp ou 8bpp)."""
    pixels = img.load()
    tile_size = 64 if is_8bpp else 32
    out = bytearray(orig_size)

    num_tiles = orig_size // tile_size
    for t in range(min(num_tiles, tiles_x * tiles_y)):
        tx = t % tiles_x
        ty = t // tiles_x
        base = t * tile_size
        for py in range(8):
            for px in range(8):
                idx = pixels[tx * 8 + px, ty * 8 + py]
                if is_8bpp:
                    out[base + py * 8 + px] = idx & 0xFF
                else:
                    byte_pos = base + py * 4 + (px // 2)
                    if px % 2 == 0:
                        out[byte_pos] = (out[byte_pos] & 0xF0) | (idx & 0x0F)
                    else:
                        out[byte_pos] = (out[byte_pos] & 0x0F) | ((idx & 0x0F) << 4)
    return bytes(out)


def extract_all(unpacked_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    for t in TARGETS:
        narc_dir = unpacked_dir / t
        files = os.listdir(narc_dir)
        ncgr_name = [f for f in files if f.endswith((".NCGR", ".NCBR"))][0]
        nclr_name = [f for f in files if f.endswith(".NCLR")][0]

        ncgr_data = (narc_dir / ncgr_name).read_bytes()
        nclr_data = (narc_dir / nclr_name).read_bytes()

        colors = parse_nclr(nclr_data)
        info = parse_ncgr(ncgr_data)
        img = decode_tiles(info["pixel_bytes"], info["tiles_x"], info["tiles_y"], info["is_8bpp"])

        # Monta paleta de 256 cores (768 bytes)
        flat_pal = []
        for i in range(256):
            if i < len(colors):
                flat_pal.extend(colors[i])
            else:
                flat_pal.extend((0, 0, 0))
        img.putpalette(flat_pal)

        rel_name = t.replace("/", "__").replace(".narc", ".png")
        out_path = out_dir / rel_name
        img.save(out_path)
        print(f"[EXTRACT] {out_path.name} ({img.width}x{img.height}, {'8bpp' if info['is_8bpp'] else '4bpp'})")


def pack_all(nitrofs_dir: Path, png_dir: Path, narc_patched_dir: Path):
    narc_patched_dir.mkdir(parents=True, exist_ok=True)
    for t in TARGETS:
        rel_name = t.replace("/", "__").replace(".narc", ".png")
        png_path = png_dir / rel_name
        if not png_path.exists():
            print(f"[SKIP] {rel_name} não encontrado")
            continue

        orig_narc_path = nitrofs_dir / t
        orig_raw = orig_narc_path.read_bytes()
        is_lz10 = len(orig_raw) > 0 and orig_raw[0] == 0x10
        narc_dec = ndspy.lz10.decompress(orig_raw) if is_lz10 else orig_raw
        narc = ndspy.narc.NARC(narc_dec)

        # Localiza o arquivo NCGR/NCBR preservando a ordem exata do NARC original
        ncgr_idx = None
        for i, fdata in enumerate(narc.files):
            fname = narc.filenames.files[i] if (hasattr(narc, "filenames") and narc.filenames and i < len(narc.filenames.files)) else ""
            if fname.endswith((".NCGR", ".NCBR")) or fdata[:4] == b"RGCN":
                ncgr_idx = i
                break
        if ncgr_idx is None:
            raise ValueError(f"NCGR/NCBR não encontrado em {t}")

        ncgr_data = bytearray(narc.files[ncgr_idx])
        info = parse_ncgr(bytes(ncgr_data))

        img = Image.open(png_path)
        if img.mode != "P":
            raise ValueError(f"{png_path.name} deve estar em modo paletizado 'P', encontrado '{img.mode}'")
        if img.size != (info["tiles_x"] * 8, info["tiles_y"] * 8):
            raise ValueError(f"{png_path.name} dimensões inválidas: {img.size}, esperado {(info['tiles_x']*8, info['tiles_y']*8)}")

        new_pixels = encode_tiles(img, info["tiles_x"], info["tiles_y"], info["is_8bpp"], info["data_size"])
        ncgr_data[info["pixel_start"] : info["pixel_start"] + info["data_size"]] = new_pixels
        narc.files[ncgr_idx] = bytes(ncgr_data)

        narc_bytes = narc.save()
        out_bytes = ndspy.lz10.compress(narc_bytes) if is_lz10 else narc_bytes

        out_narc_path = narc_patched_dir / t
        out_narc_path.parent.mkdir(parents=True, exist_ok=True)
        out_narc_path.write_bytes(out_bytes)
        print(f"[PACK] {t} -> {len(out_bytes)} bytes ({'LZ10' if is_lz10 else 'RAW'})")


def main():
    base = Path("03_TRADUCAO_ROMS_NDS/jogos/Summon Night (Japan)")
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["extract", "pack"])
    args = parser.parse_args()

    unpacked = base / "extracted" / "narc_unpacked"
    nitrofs = base / "extracted" / "nitrofs"
    png_dir = base / "extracted" / "graphics_ui"
    narc_patched = base / "build" / "narc_patched"

    if args.action == "extract":
        extract_all(unpacked, png_dir)
    elif args.action == "pack":
        pack_all(nitrofs, png_dir, narc_patched)


if __name__ == "__main__":
    main()
