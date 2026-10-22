#!/usr/bin/env python3
"""
Full Graphics Asset Extractor for Summon Night: Swordcraft Story (USA) [AB4E]
=============================================================================
Extrai todos os elementos gráficos da ROM em imagens PNG organizadas:
  - Sprites de Personagens, Armas, Inimigos e Efeitos (Archive 1)
  - Ícones de Itens, Menus, Molduras e Fontes (Archive 3)
  - Tilesets de Mapas, Dungeons e Cenários (Archive 0)
  - Paletas de Cores (PNG Swatches + JSON)
"""

import os
import struct
import json
from pathlib import Path
from PIL import Image

GBA_ROM_BASE = 0x08000000

ARCHIVE_BASES = [
    (0, 0x081FCA8C, 0x08380CCC, "maps_tilesets"),
    (1, 0x08380CCC, 0x085C10DC, "sprites_battle"),
    (3, 0x0870771C, 0x08760C21, "ui_menus_icons"),
]


def decompress_gba_lz77(data: bytes, offset: int = 0, max_out: int = 0x100000):
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
                if src >= n:
                    return None
                out.append(data[src])
                src += 1

    if len(out) != decomp_size:
        return None
    return bytes(out), src - offset


def decode_bgr555(c: int, is_transparent: bool = False):
    r = (c & 0x1F) << 3
    g = ((c >> 5) & 0x1F) << 3
    b = ((c >> 10) & 0x1F) << 3
    a = 0 if is_transparent else 255
    return (r, g, b, a)


def render_cg4(data: bytes, out_dir: Path, name_prefix: str):
    if len(data) < 0x30 or data[:4] != b"CG4 ":
        return 0

    tile_len = struct.unpack_from("<I", data, 0x14)[0]
    pal_len = struct.unpack_from("<I", data, 0x18)[0]
    num_tiles = struct.unpack_from("<I", data, 0x1C)[0]
    tile_off = struct.unpack_from("<I", data, 0x24)[0]
    pal_off = struct.unpack_from("<I", data, 0x28)[0]

    if num_tiles == 0 or tile_off + num_tiles * 32 > len(data):
        return 0

    # Parse palettes (16 colors = 32 bytes each)
    num_pals = max(1, pal_len // 32)
    palettes = []
    if pal_len >= 32 and pal_off + 32 <= len(data):
        for p in range(num_pals):
            poff = pal_off + p * 32
            if poff + 32 > len(data):
                break
            cur_pal = []
            for i in range(16):
                c = struct.unpack_from("<H", data, poff + i * 2)[0]
                cur_pal.append(decode_bgr555(c, is_transparent=(i == 0)))
            palettes.append(cur_pal)
    else:
        # Greyscale fallback
        grey_pal = [(i * 17, i * 17, i * 17, 0 if i == 0 else 255) for i in range(16)]
        palettes.append(grey_pal)

    cols = 16
    rows = (num_tiles + cols - 1) // cols
    img_w = cols * 8
    img_h = rows * 8

    saved_count = 0
    # Save main image with Palette 0, and extra variants if multiple palettes exist
    for p_idx, pal in enumerate(palettes):
        if p_idx > 4:  # limit palette variations to top 4
            break
        img = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
        for t in range(num_tiles):
            tx = (t % cols) * 8
            ty = (t // cols) * 8
            toff = tile_off + t * 32
            for y in range(8):
                row_off = toff + y * 4
                for x in range(0, 8, 2):
                    byte = data[row_off + (x // 2)]
                    p0 = byte & 0x0F
                    p1 = (byte >> 4) & 0x0F
                    img.putpixel((tx + x, ty + y), pal[p0])
                    img.putpixel((tx + x + 1, ty + y), pal[p1])

        suffix = f"_pal{p_idx}" if len(palettes) > 1 else ""
        out_path = out_dir / f"{name_prefix}{suffix}.png"
        img.save(out_path)
        saved_count += 1

    return saved_count


def render_cg8(data: bytes, out_dir: Path, name_prefix: str):
    if len(data) < 0x30 or data[:4] != b"CG8 ":
        return 0

    tile_len = struct.unpack_from("<I", data, 0x14)[0]
    pal_len = struct.unpack_from("<I", data, 0x18)[0]
    num_tiles = struct.unpack_from("<I", data, 0x1C)[0]
    tile_off = struct.unpack_from("<I", data, 0x24)[0]
    pal_off = struct.unpack_from("<I", data, 0x28)[0]

    if num_tiles == 0 or tile_off + num_tiles * 64 > len(data):
        return 0

    palette = []
    if pal_len >= 512 and pal_off + 512 <= len(data):
        for i in range(256):
            c = struct.unpack_from("<H", data, pal_off + i * 2)[0]
            palette.append(decode_bgr555(c, is_transparent=(i == 0)))
    else:
        palette = [(i, i, i, 0 if i == 0 else 255) for i in range(256)]

    cols = 16
    rows = (num_tiles + cols - 1) // cols
    img = Image.new("RGBA", (cols * 8, rows * 8), (0, 0, 0, 0))

    for t in range(num_tiles):
        tx = (t % cols) * 8
        ty = (t // cols) * 8
        toff = tile_off + t * 64
        for y in range(8):
            row_off = toff + y * 8
            for x in range(8):
                c_idx = data[row_off + x]
                img.putpixel((tx + x, ty + y), palette[c_idx])

    out_path = out_dir / f"{name_prefix}.png"
    img.save(out_path)
    return 1


def render_bit_font(data: bytes, out_dir: Path, name_prefix: str):
    if len(data) < 0x20 or data[:4] != b"BIT\x00":
        return 0
    # 12x12 font glyphs
    glyph_w, glyph_h = 12, 12
    bytes_per_glyph = 18  # 144 bits
    data_off = 0x20
    data_len = len(data) - data_off
    total_glyphs = data_len // bytes_per_glyph

    cols = 32
    rows = (total_glyphs + cols - 1) // cols
    img = Image.new("RGBA", (cols * glyph_w, rows * glyph_h), (0, 0, 0, 0))

    white = (255, 255, 255, 255)

    for g_idx in range(total_glyphs):
        gx = (g_idx % cols) * glyph_w
        gy = (g_idx // cols) * glyph_h
        goff = data_off + g_idx * bytes_per_glyph

        bit_pos = 0
        for y in range(glyph_h):
            for x in range(glyph_w):
                byte_idx = goff + (bit_pos >> 3)
                bit_in_byte = 7 - (bit_pos & 7)
                if byte_idx < len(data) and (data[byte_idx] & (1 << bit_in_byte)):
                    img.putpixel((gx + x, gy + y), white)
                bit_pos += 1

    out_path = out_dir / f"{name_prefix}_vwf_font.png"
    img.save(out_path)
    return 1


def render_pal_swatch(data: bytes, out_dir: Path, name_prefix: str):
    # PAL or PLA file
    colors = []
    # Search for BGR555 color stream
    start_off = 0x10 if len(data) >= 0x20 else 0
    num_colors = (len(data) - start_off) // 2
    if num_colors < 16:
        return 0
    num_colors = min(num_colors, 256)

    for i in range(num_colors):
        c = struct.unpack_from("<H", data, start_off + i * 2)[0]
        colors.append(decode_bgr555(c, is_transparent=False))

    swatch_size = 16
    cols = 16
    rows = (num_colors + cols - 1) // cols
    img = Image.new("RGBA", (cols * swatch_size, rows * swatch_size), (0, 0, 0, 255))

    for i, col in enumerate(colors):
        cx = (i % cols) * swatch_size
        cy = (i // cols) * swatch_size
        for dy in range(swatch_size):
            for dx in range(swatch_size):
                img.putpixel((cx + dx, cy + dy), col)

    out_path = out_dir / f"{name_prefix}_palette.png"
    img.save(out_path)
    return 1


def process_file_blob(blob: bytes, out_dir: Path, prefix: str):
    count = 0
    # Check if LZ77 compressed
    if len(blob) > 4 and blob[0] == 0x10:
        res = decompress_gba_lz77(blob)
        if res:
            blob = res[0]

    magic = blob[:4]
    if magic == b"CG4 ":
        count += render_cg4(blob, out_dir, prefix)
    elif magic == b"CG8 ":
        count += render_cg8(blob, out_dir, prefix)
    elif magic == b"BIT\x00":
        count += render_bit_font(blob, out_dir, prefix)
    elif magic in (b"PAL ", b"PLA "):
        count += render_pal_swatch(blob, out_dir, prefix)
    elif len(blob) >= 8:
        # Check for nested sub-archive: [num_entries (u16), 0x0001 (u16), 0x00000004 (u32)]
        num_sub, ver, sub_w1 = struct.unpack_from("<HHI", blob, 0)
        if ver == 1 and sub_w1 == 4 and 0 < num_sub < 1000:
            sub_dir = out_dir / prefix
            sub_dir.mkdir(parents=True, exist_ok=True)
            for s in range(num_sub):
                table_entry = 8 + s * 8
                if table_entry + 8 > len(blob):
                    break
                soff_u, ssz_u = struct.unpack_from("<II", blob, table_entry)
                s_off = soff_u << 4
                s_sz = ssz_u << 4
                if s_sz == 0 or s_off + s_sz > len(blob):
                    continue
                sub_blob = blob[s_off : s_off + s_sz]
                count += process_file_blob(sub_blob, sub_dir, f"sub_{s:03d}")

    return count


def main():
    rom_path = Path("rom/Summon Night - Swordcraft Story (USA).gba")
    if not rom_path.exists():
        print(f"[!] ROM not found at {rom_path}")
        return 1

    rom = rom_path.read_bytes()
    base_out = Path("extracted/graphics")
    base_out.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print(" Summon Night: Swordcraft Story - Extração Completa de Gráficos")
    print("=================================================================")

    total_images = 0

    for aid, base_addr, limit_addr, folder_name in ARCHIVE_BASES:
        out_dir = base_out / folder_name
        out_dir.mkdir(parents=True, exist_ok=True)

        base_off = base_addr - GBA_ROM_BASE
        first_off = struct.unpack_from("<I", rom, base_off + 8)[0] << 4
        num_files = (first_off - 8) // 8

        print(f"\n[+] Processando {folder_name} ({num_files} arquivos)...")
        arch_images = 0

        for f_idx in range(num_files):
            entry_off = base_off + 8 + f_idx * 8
            off_u, sz_u = struct.unpack_from("<II", rom, entry_off)
            boff = base_off + (off_u << 4)
            bsz = sz_u << 4
            if bsz == 0 or boff + bsz > len(rom):
                continue

            raw = rom[boff : boff + bsz]
            prefix = f"file_{f_idx:04d}"
            extracted = process_file_blob(raw, out_dir, prefix)
            arch_images += extracted

        print(f"    -> Concluído {folder_name}: {arch_images} imagens PNG geradas.")
        total_images += arch_images

    print("\n=================================================================")
    print(f"[SUCESSO] Total de imagens PNG extraídas: {total_images}")
    print(f"Arquivos salvos em: {base_out.resolve()}")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    exit(main())
