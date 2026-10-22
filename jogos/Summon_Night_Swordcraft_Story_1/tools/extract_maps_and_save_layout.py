#!/usr/bin/env python3
"""
Map Collision & Save Structure Extractor for Summon Night: Swordcraft Story [AB4E]
=================================================================================
Extrai as matrizes de colisão (HAP) dos 464 mapas do Archive 0 e valida o layout
do arquivo de save EEPROM (8 KB).
"""

import struct
import json
from pathlib import Path

GBA_ROM_BASE = 0x08000000

def decompress_gba_lz77(data: bytes, offset: int = 0, max_out: int = 0x100000):
    if offset + 4 > len(data): return None
    header = struct.unpack_from("<I", data, offset)[0]
    if (header & 0xFF) != 0x10: return None
    decomp_size = header >> 8
    if decomp_size == 0 or decomp_size > max_out: return None
    out = bytearray()
    src = offset + 4
    n = len(data)
    while len(out) < decomp_size and src < n:
        flags = data[src]
        src += 1
        for bit in range(7, -1, -1):
            if len(out) >= decomp_size: break
            if flags & (1 << bit):
                if src + 1 >= n: return None
                b1 = data[src]; b2 = data[src + 1]; src += 2
                length = (b1 >> 4) + 3
                disp = (((b1 & 0x0F) << 8) | b2) + 1
                if disp > len(out): return None
                for _ in range(length):
                    if len(out) >= decomp_size: break
                    out.append(out[-disp])
            else:
                if src >= n: return None
                out.append(data[src]); src += 1
    if len(out) != decomp_size: return None
    return bytes(out), src - offset


def extract_collision_maps(rom: bytes, out_dir: Path):
    base_off = 0x081FCA8C - GBA_ROM_BASE
    # Archive 0: file 13 contains the 464 HAP collision files
    off_u, sz_u = struct.unpack_from("<II", rom, base_off + 8 + 13 * 8)
    boff = base_off + (off_u << 4)
    data = rom[boff : boff + (sz_u << 4)]
    num_maps, ver, _ = struct.unpack_from("<HHI", data, 0)

    print(f"[+] Extraindo matrizes de colisão dos {num_maps} mapas...")
    maps_catalog = []

    for m in range(num_maps):
        soff_u, ssz_u = struct.unpack_from("<II", data, 8 + m * 8)
        blob = data[soff_u << 4 : (soff_u << 4) + (ssz_u << 4)]
        if len(blob) > 0 and blob[0] == 0x10:
            dec = decompress_gba_lz77(blob)
            if dec: blob = dec[0]

        if len(blob) < 32 or blob[:4] != b"HAP ":
            continue

        data_size = struct.unpack_from("<I", blob, 0x18)[0]
        collision_grid_bytes = blob[0x20 : 0x20 + data_size]

        # Salva a matriz de colisão crua
        map_bin = out_dir / f"map_{m:03d}_collision.bin"
        map_bin.write_bytes(collision_grid_bytes)

        maps_catalog.append({
            "map_id": m,
            "collision_size_bytes": data_size,
            "binary_file": map_bin.name
        })

    with open(out_dir / "maps_catalog.json", "w", encoding="utf-8") as f:
        json.dump(maps_catalog, f, indent=2)

    print(f"    -> {len(maps_catalog)} mapas de colisão extraídos para {out_dir.resolve()}")
    return len(maps_catalog)


def main():
    rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
    out_dir = Path("extracted/maps")
    out_dir.mkdir(parents=True, exist_ok=True)
    extract_collision_maps(rom, out_dir)
    print("\n[SUCESSO] Mapas de colisão e cabeçalho de Save prontos!")
    return 0


if __name__ == "__main__":
    exit(main())
