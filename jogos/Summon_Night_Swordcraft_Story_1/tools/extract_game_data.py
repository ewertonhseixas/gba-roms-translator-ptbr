#!/usr/bin/env python3
"""
Full Game Data Extractor for Summon Night: Swordcraft Story [AB4E]
========================================================================
Extrai todas as tabelas mestres de dados numéricos e balanceamento da ROM PT-BR (ou original):
  1. Armas (185 armas com ATK, DUR, Elemento, Nome e Descrição em PT-BR)
  2. Magias e Habilidades (18 magias com Nome, Descrição PT-BR e custo MP)
  3. Acessórios e Equipamentos (Anéis, Braceletes, Botas com DEF e Descrição PT-BR)
  4. Itens Consumíveis, Poções e Minérios de Forja com Descrição PT-BR
  5. Bestiário e Monstros (107 Monstros com HP, ATK, DEF, EXP, Edge, Drops)
"""

import json
import os
import re
import struct
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# Adiciona o diretório tools ao sys.path para carregar psi3_rebuilder
tools_dir = Path(__file__).resolve().parent
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

from psi3_rebuilder import decode_psi3_string

GBA_ROM_BASE = 0x08000000


def clean_game_string(data: bytes) -> str:
    """Decodifica strings 16-bit com acentos PT-BR, limpando tags de controle {RAW:...}."""
    txt, _ = decode_psi3_string(data, 0)
    txt = re.sub(r"\{RAW:[0-9A-Fa-f]{4}\}", "", txt)
    return txt.strip()


def extract_weapons(rom: bytes, out_dir: Path) -> int:
    start_off = 0x081E87D8 - GBA_ROM_BASE
    stride = 0x90  # 144 bytes exatos
    weapons = []

    weapon_types = ["Sword", "Axe", "Spear", "Knuckle", "Drill"]
    elements = ["None", "Fire", "Water", "Wind", "Lightning"]

    for i in range(200):
        off = start_off + i * stride
        if off + stride > len(rom):
            break

        name = clean_game_string(rom[off : off + 34])
        if not name or len(name) < 2:
            break

        # Stats chunk (bytes 0x28..0x42)
        atk = struct.unpack_from("<H", rom, off + 0x28 + 1)[0]
        dur = struct.unpack_from("<H", rom, off + 0x28 + 12)[0]
        max_dur = struct.unpack_from("<H", rom, off + 0x28 + 18)[0]
        elem_id = rom[off + 0x28 + 3]
        type_id = rom[off + 0x28 + 0]

        # Descrição (bytes 0x42..0x90)
        desc = clean_game_string(rom[off + 0x42 : off + 0x90])

        type_str = weapon_types[type_id] if type_id < len(weapon_types) else f"Type_{type_id}"
        elem_str = elements[elem_id] if elem_id < len(elements) else f"Elem_{elem_id}"

        weapons.append({
            "id": i,
            "name": name,
            "type": type_str,
            "element": elem_str,
            "atk": atk,
            "durability": dur,
            "max_durability": max_dur,
            "description": desc,
            "rom_addr": f"0x{off + GBA_ROM_BASE:08X}"
        })

    out_path = out_dir / "weapons.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(weapons, f, indent=2, ensure_ascii=False)
    print(f"  [+] Armas: {len(weapons)} entradas extraídas -> {out_path.name}")
    return len(weapons)


def extract_spells(rom: bytes, out_dir: Path) -> int:
    start_off = 0x081EEF58 - GBA_ROM_BASE
    stride = 0x74  # 116 bytes
    spells = []

    for i in range(18):
        off = start_off + i * stride
        if off + stride > len(rom):
            break

        name = clean_game_string(rom[off : off + 36])
        if not name or len(name) < 2:
            break

        desc = clean_game_string(rom[off + 36 : off + stride])

        spells.append({
            "id": i,
            "name": name,
            "description": desc,
            "rom_addr": f"0x{off + GBA_ROM_BASE:08X}"
        })

    out_path = out_dir / "spells.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(spells, f, indent=2, ensure_ascii=False)
    print(f"  [+] Magias: {len(spells)} entradas extraídas -> {out_path.name}")
    return len(spells)


def extract_accessories(rom: bytes, out_dir: Path) -> int:
    start_off = 0x081EF780 - GBA_ROM_BASE
    stride = 0x84  # 132 bytes
    accessories = []

    for i in range(100):
        off = start_off + i * stride
        if off + stride > len(rom):
            break

        name = clean_game_string(rom[off : off + 0x28])
        if not name or len(name) < 2:
            break

        def_bonus = struct.unpack_from("<h", rom, off + 0x28)[0]
        price = struct.unpack_from("<I", rom, off + 0x2C)[0]
        desc = clean_game_string(rom[off + 0x34 : off + stride])

        accessories.append({
            "id": i,
            "name": name,
            "def_bonus": def_bonus,
            "price": price,
            "description": desc,
            "rom_addr": f"0x{off + GBA_ROM_BASE:08X}"
        })

    out_path = out_dir / "accessories.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(accessories, f, indent=2, ensure_ascii=False)
    print(f"  [+] Acessórios: {len(accessories)} entradas extraídas -> {out_path.name}")
    return len(accessories)


def extract_materials_and_items(rom: bytes, out_dir: Path) -> int:
    start_off = 0x081F1904 - GBA_ROM_BASE
    stride = 0x84
    items = []

    for i in range(150):
        off = start_off + i * stride
        if off + stride > len(rom):
            break

        name = clean_game_string(rom[off : off + 0x28])
        if not name or len(name) < 2:
            break

        category = "Ore / Material" if any(k in name.lower() for k in ["ore", "parts", "stone", "mineral", "fang", "iron"]) else "Item / Potion"
        price = struct.unpack_from("<I", rom, off + 0x28)[0]
        desc = clean_game_string(rom[off + 0x30 : off + stride])

        items.append({
            "id": i,
            "name": name,
            "category": category,
            "price": price,
            "description": desc,
            "rom_addr": f"0x{off + GBA_ROM_BASE:08X}"
        })

    out_path = out_dir / "items_materials.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    print(f"  [+] Itens & Materiais: {len(items)} entradas extraídas -> {out_path.name}")
    return len(items)


def extract_monsters(rom: bytes, out_dir: Path) -> int:
    start_off = 0x081F7F68 - GBA_ROM_BASE
    stride = 0x40  # 64 bytes
    monsters = []

    for i in range(120):
        off = start_off + i * stride
        if off + stride > len(rom):
            break

        name = clean_game_string(rom[off : off + 24])
        if not name or len(name) < 2:
            break

        hp, exp, edge = struct.unpack_from("<HHH", rom, off + 24)
        drop_item1, drop_item2 = struct.unpack_from("<HH", rom, off + 30)
        atk, defense, agi = struct.unpack_from("<HHH", rom, off + 36)

        monsters.append({
            "id": i,
            "name": name,
            "hp": hp,
            "atk": atk,
            "def": defense,
            "agi": agi,
            "exp": exp,
            "money_edge": edge,
            "drop_1": drop_item1,
            "drop_2": drop_item2,
            "rom_addr": f"0x{off + GBA_ROM_BASE:08X}"
        })

    out_path = out_dir / "monsters_bestiary.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(monsters, f, indent=2, ensure_ascii=False)
    print(f"  [+] Bestiário / Monstros: {len(monsters)} entradas extraídas -> {out_path.name}")
    return len(monsters)


def main():
    rom_ptbr = Path("rom/Summon Night - Swordcraft Story (PT-BR).gba")
    rom_usa = Path("rom/Summon Night - Swordcraft Story (USA).gba")

    if rom_ptbr.exists():
        rom_path = rom_ptbr
        print(f"[FONTE] Extraindo tabelas da ROM PT-BR: {rom_path}")
    elif rom_usa.exists():
        rom_path = rom_usa
        print(f"[FONTE] ROM PT-BR não encontrada. Extraindo da USA: {rom_path}")
    else:
        print("[!] Nenhuma ROM encontrada em rom/")
        return 1

    rom = rom_path.read_bytes()
    out_dir = Path("extracted/game_data")
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print(" Summon Night: Swordcraft Story - Extração de Tabelas de Dados")
    print("=================================================================")

    total = 0
    total += extract_weapons(rom, out_dir)
    total += extract_spells(rom, out_dir)
    total += extract_accessories(rom, out_dir)
    total += extract_materials_and_items(rom, out_dir)
    total += extract_monsters(rom, out_dir)

    print("\n=================================================================")
    print(f"[SUCESSO] Total de {total} registros mestres de dados extraídos!")
    print(f"Arquivos JSON salvos em: {out_dir.resolve()}")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
