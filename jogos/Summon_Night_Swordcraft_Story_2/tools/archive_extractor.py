#!/usr/bin/env python3
"""
GBA Archive FS & LZ77 Extractor + Script/Text Inspector
Summon Night: Swordcraft Story 2 (USA) [BSKE]
=========================================================
Lê os 5 Archives principais da ROM de Summon Night 2:
  - Archive 0: 0x085015CC (Mapas, Cenários e Sub-contêineres de eventos)
  - Archive 1: 0x08C7F5FC (Sprites de Batalha e Monstros)
  - Archive 2: 0x08ABA81C (Scripts de Diálogos e Eventos PSI3 - 2.551 arquivos)
  - Archive 3: 0x089436FC (Fontes BIT0, Menus e Interface)
  - Archive 4: 0x08FB6DEC (Áudios e HUD)
"""

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

GBA_ROM_BASE = 0x08000000

ARCHIVE_BASES = [
    (0, 0x085015CC, 0x089436FC, "Archive0_Maps_Tilesets_Events"),
    (1, 0x08C7F5FC, 0x08FB6DEC, "Archive1_Sprites_Battle"),
    (2, 0x08ABA81C, 0x08C7F5FC, "Archive2_Scripts_Dialogues_PSI3"),
    (3, 0x089436FC, 0x08ABA81C, "Archive3_UI_Fonts_BIT0"),
    (4, 0x08FB6DEC, 0x08FCC05C, "Archive4_Audio_HUD"),
]


def decompress_gba_lz77(data: bytes, offset: int = 0, max_out: int = 0x80000) -> Optional[Tuple[bytes, int]]:
    """
    Descomprime um bloco no formato LZ77 padrão da BIOS do GBA (SWI 0x11 / 0x12).
    Header de 32 bits: [7:0] = 0x10 (magic LZ77), [31:8] = tamanho descomprimido.
    """
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
    return (bytes(out), src - offset)


def parse_archive_table(rom: bytes, base_rom_addr: int, limit_rom_addr: int) -> List[Dict[str, Any]]:
    base_off = base_rom_addr - GBA_ROM_BASE
    limit_off = limit_rom_addr - GBA_ROM_BASE

    hdr0, hdr1 = struct.unpack_from("<II", rom, base_off)
    first_off_units, first_size_units = struct.unpack_from("<II", rom, base_off + 8)
    first_byte_off = first_off_units << 4
    max_entries = (first_byte_off - 8) // 8 if first_byte_off >= 16 else 0

    entries = []
    for idx in range(max_entries):
        ent_off = base_off + 8 + idx * 8
        off_u16, size_u16 = struct.unpack_from("<II", rom, ent_off)
        byte_off = off_u16 << 4
        byte_size = size_u16 << 4

        if byte_off == 0 and byte_size == 0:
            continue
        if base_off + byte_off >= len(rom) or base_off + byte_off + byte_size > len(rom):
            break

        file_rom_addr = base_rom_addr + byte_off
        file_rom_off = base_off + byte_off
        raw_head = rom[file_rom_off : file_rom_off + 16]
        is_lz77 = len(raw_head) >= 4 and raw_head[0] == 0x10
        decomp_len = (struct.unpack_from("<I", raw_head, 0)[0] >> 8) if is_lz77 else 0

        entries.append({
            "index": idx,
            "rom_addr": f"0x{file_rom_addr:08X}",
            "file_offset": file_rom_off,
            "compressed_size": byte_size,
            "is_lz77": is_lz77,
            "lz77_decomp_size": decomp_len if is_lz77 else None,
            "head_hex": raw_head[:8].hex().upper(),
        })

    return entries


def main():
    root = Path(__file__).resolve().parent.parent
    rom_file = root / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
    if not rom_file.exists():
        print(f"ROM não encontrada em {rom_file}")
        return

    rom = rom_file.read_bytes()
    print("=" * 70)
    print(" SUMMON NIGHT: SWORDCRAFT STORY 2 - INSPEÇÃO DOS ARCHIVES")
    print("=" * 70)
    for arch_id, base, limit, label in ARCHIVE_BASES:
        entries = parse_archive_table(rom, base, limit)
        lz_count = sum(1 for e in entries if e["is_lz77"])
        print(f"[{arch_id}] {label:<35} @ 0x{base:08X}: {len(entries)} arquivos ({lz_count} LZ77)")


if __name__ == "__main__":
    main()
