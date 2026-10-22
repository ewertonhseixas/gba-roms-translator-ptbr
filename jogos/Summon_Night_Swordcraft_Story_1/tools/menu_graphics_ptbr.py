#!/usr/bin/env python3
"""
menu_graphics_ptbr.py
=====================
Mantém o menu de pausa e cabeçalhos gráficos 100% no original em inglês (USA),
conforme solicitado pelo usuário, restaurando com perfeição os arquivos do Archive 3
e revertendo quaisquer patches de ladrilhos de menu.
"""

import struct
from pathlib import Path

ARCH3_BASE = 0x0870771C - 0x08000000


def get_archive3_file_range(rom: bytearray, file_idx: int):
    off_u, sz_u = struct.unpack_from('<II', rom, ARCH3_BASE + 8 + file_idx * 8)
    boff = ARCH3_BASE + (off_u << 4)
    bsz = sz_u << 4
    return boff, bsz


def restore_english_menu_graphics(rom: bytearray, rom_usa: bytes):
    """
    Restaura Entry 4, Entry 10 (cabeçalhos do menu de pausa) e Entry 20
    ao estado 100% original USA em inglês.
    """
    for file_idx in [4, 10, 20]:
        boff, bsz = get_archive3_file_range(rom, file_idx)
        rom[boff : boff + bsz] = rom_usa[boff : boff + bsz]
    print("  [+] Gráficos de menu (Archive 3, Entries 4, 10, 20) mantidos no original USA em inglês.")


def revert_event_item_tile_patch(rom: bytearray):
    """
    Restaura o código original de montagem em 0x08038B1C:
    'movs r1, #0x9c' (Tile 156 = ITEM).
    """
    addr = 0x00038B1C
    if rom[addr:addr+2] == b'\xa5\x21':
        rom[addr:addr+2] = b'\x9c\x21'
        print("  [+] Rotina em 0x08038B1C restaurada ao original USA (Tile 156 / ITEM).")


def patch_floor_indicator(rom: bytearray):
    """Muda 'F' (0x8265) para 'A' (0x8260) em 0x08073154 para Casa 2A."""
    addr = 0x08073154 - 0x08000000
    if rom[addr:addr+2] == b'\x82\x65':
        rom[addr:addr+2] = b'\x82\x60'
        print("  [+] Indicador de Andar atualizado: 'F' -> 'A' (2A / 2º Andar)")


def apply_all_menu_patches(rom: bytearray, rom_usa: bytes = None):
    print("Processando gráficos de Interface e Telas...")
    if rom_usa is not None:
        restore_english_menu_graphics(rom, rom_usa)
    revert_event_item_tile_patch(rom)
    patch_floor_indicator(rom)


if __name__ == "__main__":
    rom_path = Path("rom/Summon Night - Swordcraft Story (PT-BR).gba")
    usa_path = Path("rom/Summon Night - Swordcraft Story (USA).gba")
    rom = bytearray(rom_path.read_bytes())
    rom_usa = usa_path.read_bytes()
    apply_all_menu_patches(rom, rom_usa)
    try:
        rom_path.write_bytes(rom)
    except OSError:
        with rom_path.open("r+b") as f:
            f.seek(0)
            f.write(rom)
    print(f"Salvo em {rom_path} ({len(rom)} bytes)")
