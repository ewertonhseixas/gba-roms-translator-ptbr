#!/usr/bin/env python3
"""
Compilador Unificado da Tradução PT-BR (UI + Armas + Magias + Itens + Bestiário + Diálogos PSI3 + Fonte BIT\0)
Summon Night: Swordcraft Story (USA) [AB4E]
==============================================================================================================
Lê diretamente todas as tabelas traduzidas e validadas em `ARQUIVOS md/03..09.md` (e `extracted/translation_pack_ptbr.json`),
compilando uma ROM completa em Português (`rom/Summon Night - Swordcraft Story (PT-BR).gba`):
  1. Injeta os 24 glifos acentuados PT-BR (12x12 1bpp) na fonte `BIT\0` (`0x08707808`) e na tabela `0x081DB270`.
  2. Compila as 179 strings de Interface, Batalha, Forja, Lojas, Link e Sistema (`03-interface...`),
     fazendo escrita in-place quando cabe ou realocando para o espaço livre (`0x08760C2C+`) e atualizando
     automaticamente todos os ponteiros de 32 bits (`0x0807xxxx`) na ROM!
  3. Compila os Nomes e Descrições de todas as Armas (`04`, `05`), Magias (`05`), Itens (`06`) e Monstros (`07`)
     nas tabelas de structs da ROM (`0x081E87D8`–`0x081F9D28`).
  4. Compila todos os diálogos de eventos `PSI3` (`08` e `09`), recalculando todos os 14 opcodes de salto/callback,
     comprimindo via LZ77 da BIOS (`0x10`) e atualizando o diretório do Archive #2 (`0x085C10DC`).
"""

import json
import re
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from archive_extractor import parse_archive_table, decompress_gba_lz77
from font_ptbr_injector import inject_ptbr_font_into_rom
from menu_graphics_ptbr import apply_all_menu_patches
from psi3_rebuilder import (
    ARCHIVE2_BASE_ADDR,
    ARCHIVE2_LIMIT_ADDR,
    DEFAULT_FREE_SPACE_ADDR,
    GBA_ROM_BASE,
    build_opcode_spec_table,
    decode_psi3_string,
    encode_psi3_string,
    extract_psi3_strings,
    rebuild_psi3_script,
    reinsert_scripts_into_rom,
)

sys.stdout.reconfigure(encoding="utf-8")


PROJECT_VERSION = "v0.2.5"


def create_ips_patch(src_bytes: bytes, dst_bytes: bytes, out_path: Path) -> int:
    """Gera um arquivo de patch IPS padrão a partir das duas ROMs."""
    out = bytearray(b'PATCH')
    i = 0
    n = max(len(src_bytes), len(dst_bytes))
    while i < n:
        b_src = src_bytes[i] if i < len(src_bytes) else None
        b_dst = dst_bytes[i] if i < len(dst_bytes) else None
        if b_src != b_dst:
            start = i
            diff = bytearray()
            while i < n and (len(diff) < 0xFFFF):
                s = src_bytes[i] if i < len(src_bytes) else None
                d = dst_bytes[i] if i < len(dst_bytes) else None
                if s == d:
                    ahead_same = True
                    for k in range(1, 6):
                        if i + k < n:
                            if (src_bytes[i+k] if i+k < len(src_bytes) else None) != (dst_bytes[i+k] if i+k < len(dst_bytes) else None):
                                ahead_same = False
                                break
                    if ahead_same:
                        break
                diff.append(d)
                i += 1
            out += struct.pack('>I', start)[1:] # 3 bytes offset
            out += struct.pack('>H', len(diff)) # 2 bytes size
            out += diff
        else:
            i += 1
    out += b'EOF'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    return len(out)


def clean_md_cell(cell: str) -> str:
    """Remove formatação markdown (`code`, *italics*) de uma célula de tabela."""
    s = cell.strip()
    if s.startswith("`") and s.endswith("`") and s.count("`") == 2:
        return s[1:-1]
    return s


def extract_backtick_lines(cell: str) -> List[str]:
    """
    Extrai linhas de texto envolvidas em crases (`...`) separadas por <br> ou / em uma célula Markdown.
    Remove anotações como *(Protagonista:)* fora ou dentro das crases.
    """
    parts = re.split(r"<br\s*/?>", cell)
    lines: List[str] = []
    for p in parts:
        # Remove prefixos de anotação como *(Protagonista:)* ou *(Escolha 1)*
        p_clean = re.sub(r"\*\([^)]+\)\*\s*", "", p).strip()
        bt_matches = re.findall(r"`([^`]+)`", p_clean)
        if bt_matches:
            # Se for algo como `Yes, Master.` / `Alright.` na mesma linha, separa
            for m in bt_matches:
                m_clean = re.sub(r"^\*\([^)]+\)\*\s*", "", m)
                m_clean = m_clean.replace("*", "")
                if " / " in m_clean and "` / `" not in p_clean:
                    for sub in m_clean.split(" / "):
                        lines.append(sub.strip())
                else:
                    lines.append(m_clean)
        elif p_clean:
            p_clean = p_clean.replace("`", "").replace("*", "").strip()
            if p_clean and p_clean != "...":
                lines.append(p_clean)
    return lines


def find_slot_capacity_bytes(rom: bytes, start_off: int, max_scan: int = 160) -> Tuple[str, int]:
    """
    Lê a string Shift-JIS original em `start_off` e calcula quantos bytes (incluindo padding 0x0000)
    existem antes do próximo dado não-zero.
    """
    orig_text, after_null = decode_psi3_string(rom, start_off)
    pos = after_null
    while pos < len(rom) and (pos - start_off) < max_scan:
        hw = struct.unpack_from("<H", rom, pos)[0]
        if hw != 0x0000:
            break
        pos += 2
    return (orig_text, pos - start_off)


def build_rom_pointer_index(rom: bytes) -> Dict[int, List[int]]:
    """
    Mapeia todos os ponteiros alinhados de 32 bits (0x08XXXXXX) na área de código/tabelas da ROM
    (0x08000000..0x08200000) para suas posições no arquivo.
    """
    ptr_map: Dict[int, List[int]] = {}
    for off in range(0, 0x00200000, 4):
        val = struct.unpack_from("<I", rom, off)[0]
        if 0x08070000 <= val < 0x08200000:
            ptr_map.setdefault(val, []).append(off)
    return ptr_map


def match_ellipsis_style(orig_text: str, ptbr_text: str) -> str:
    """
    Se a string original usava o glifo duplo de reticências `…` (0x8163 + 0x84AD),
    converte `...` na tradução PT-BR para `…`. Se usava `...` ASCII, mantém `...`.
    """
    if "…" in orig_text and "..." in ptbr_text:
        return ptbr_text.replace("...", "…")
    if "..." in orig_text and "…" in ptbr_text and "…" not in orig_text:
        return ptbr_text.replace("…", "...")
    return ptbr_text


def apply_ui_and_system_md(
    rom_mut: bytearray,
    orig_rom: bytes,
    md_path: Path,
    ptr_index: Dict[int, List[int]],
    free_space_off: int,
) -> Tuple[int, Dict[str, int]]:
    """
    Aplica todas as traduções de `03-interface-menus-batalha-e-sistema.md`.
    Se a tradução couber no espaço original, grava in-place; se for maior, realoca para
    `free_space_off` e atualiza todos os ponteiros 32-bit na ROM!
    """
    stats = {"in_place": 0, "repointed": 0, "ptrs_updated": 0}
    lines = md_path.read_text(encoding="utf-8").splitlines()

    for line in lines:
        if not line.startswith("|") or "---" in line or "Endereço ROM" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 3:
            continue
        addr_strs = re.findall(r"0x08[0-9A-Fa-f]{6}", cols[0])
        if not addr_strs:
            continue

        en_text = clean_md_cell(cols[1])
        ptbr_text = clean_md_cell(cols[2])
        if not ptbr_text:
            continue

        for addr_s in addr_strs:
            rom_addr = int(addr_s, 16)
            rom_off = rom_addr - GBA_ROM_BASE
            orig_decoded, cap_bytes = find_slot_capacity_bytes(orig_rom, rom_off)
            ptbr_styled = match_ellipsis_style(orig_decoded, ptbr_text)
            enc = encode_psi3_string(ptbr_styled)

            if len(enc) <= cap_bytes:
                # Grava in-place preenchendo o restante da capacidade original com 0x00
                rom_mut[rom_off : rom_off + len(enc)] = enc
                stats["in_place"] += 1
            else:
                # Aloca no espaço livre (alinhado em 4 bytes) e atualiza os ponteiros 32-bit!
                free_space_off = (free_space_off + 3) & ~3
                new_rom_addr = GBA_ROM_BASE + free_space_off
                rom_mut[free_space_off : free_space_off + len(enc)] = enc
                free_space_off += len(enc)

                ptr_offs = ptr_index.get(rom_addr, [])
                for p_off in ptr_offs:
                    struct.pack_into("<I", rom_mut, p_off, new_rom_addr)
                    stats["ptrs_updated"] += 1
                stats["repointed"] += 1

    return (free_space_off, stats)


def fit_fixed_struct_string(ptbr_text: str, max_bytes: int) -> bytes:
    """
    Codifica `ptbr_text` garantindo que caiba em `max_bytes` (incluindo o terminador 0x0000 de 2 bytes).
    Se ultrapassar por 1..4 caracteres, aplica abreviações inteligentes de RPG antes de truncar.
    """
    enc = encode_psi3_string(ptbr_text)
    if len(enc) <= max_bytes:
        return enc

    s = ptbr_text
    for long_w, short_w in [
        (" com o elemento ", " c/ elem. "),
        (" com elemento ", " c/ elem. "),
        (" com ", " c/ "),
        (" para ", " p/ "),
        (" temporariamente", " temp."),
        (" fortalecida", " fort."),
        (" fortalecido", " fort."),
        (" aprimorada", " aprim."),
        (" aprimorado", " aprim."),
        (" todos os inimigos", " todos inim."),
        (" pontos de vida (HP)", " HP"),
    ]:
        if long_w in s:
            s = s.replace(long_w, short_w)
            enc = encode_psi3_string(s)
            if len(enc) <= max_bytes:
                return enc

    # Trunca no limite exato de halfwords (2 bytes por char + 2 bytes de 0x0000)
    return enc[: max_bytes - 2] + b"\x00\x00"


def apply_catalog_structs_md(rom_mut: bytearray, md_dir: Path) -> Dict[str, int]:
    """
    Aplica as traduções das tabelas de structs de tamanho fixo:
      - 04-armas-espadas-machados-e-lancas.md (WeaponDataEntry: name=34B, desc=78B)
      - 05-armas-soqueiras-brocas-e-magias.md (WeaponDataEntry / SpellDataEntry: name=34B, desc=78B/80B)
      - 06-itens-acessorios-materiais-e-chave.md (ItemDataEntry: name=34B, desc=80B)
      - 07-bestiario-monstros-e-chefes.md (MonsterDataEntry: name=30B)
    """
    counts = {"weapons_spells_items": 0, "monsters": 0}

    for md_name in [
        "04-armas-espadas-machados-e-lancas.md",
        "05-armas-soqueiras-brocas-e-magias.md",
        "06-itens-acessorios-materiais-e-chave.md",
    ]:
        lines = (md_dir / md_name).read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line.startswith("|") or "---" in line or "Endereço" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 5:
                continue
            m = re.search(r"(0x08[0-9A-Fa-f]{6})\s*`\s*/\s*`\s*([0-9A-Fa-f]{4})", cols[0])
            if not m:
                continue
            name_addr = int(m.group(1), 16)
            desc_low = int(m.group(2), 16)
            desc_addr = (name_addr & 0xFFFF0000) | desc_low
            if desc_addr < name_addr:
                desc_addr += 0x10000

            ptbr_name = clean_md_cell(cols[3])
            ptbr_desc = clean_md_cell(cols[4])

            # Determina capacidades exatas da struct (descrições têm limite estrito de 36 chars = 74 bytes c/ null na engine em 0x08009E30)
            name_max_bytes = 34  # 16 chars + null
            desc_max_bytes = 74  # 36 chars + null (evita travamento quando r4[4] > r4[9]=37)
            desc_slot_bytes = 78 if name_addr < 0x081EEF58 else 80

            if ptbr_name:
                enc_name = fit_fixed_struct_string(ptbr_name, name_max_bytes)
                n_off = name_addr - GBA_ROM_BASE
                rom_mut[n_off : n_off + name_max_bytes] = enc_name.ljust(name_max_bytes, b"\x00")

            if ptbr_desc:
                enc_desc = fit_fixed_struct_string(ptbr_desc, desc_max_bytes)
                d_off = desc_addr - GBA_ROM_BASE
                rom_mut[d_off : d_off + desc_slot_bytes] = enc_desc.ljust(desc_slot_bytes, b"\x00")

            counts["weapons_spells_items"] += 1

    # 07-bestiario-monstros-e-chefes.md
    lines_07 = (md_dir / "07-bestiario-monstros-e-chefes.md").read_text(encoding="utf-8").splitlines()
    for line in lines_07:
        if not line.startswith("|") or "---" in line or "Endereço ROM" in line:
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 3:
            continue
        m = re.search(r"0x08[0-9A-Fa-f]{6}", cols[0])
        if not m:
            continue
        m_addr = int(m.group(0), 16)
        ptbr_name = clean_md_cell(cols[2])
        if ptbr_name:
            enc_name = fit_fixed_struct_string(ptbr_name, 30)
            m_off = m_addr - GBA_ROM_BASE
            rom_mut[m_off : m_off + 30] = enc_name.ljust(30, b"\x00")
            counts["monsters"] += 1

    return counts


def parse_dialogue_mds(
    orig_rom: bytes,
    specs: Dict[int, List[str]],
    entries: List[Dict[str, Any]],
    md_paths: List[Path],
) -> Dict[int, Dict[int, str]]:
    """
    Extrai todos os pares (linha_EN -> linha_PTBR) de `08-dialogos...` e `09-dialogos...`
    e os associa aos `string_index` exatos de cada script `PSI3`!
    """
    # Carrega as strings originais de cada script mencionado nos MDs
    script_orig_strings: Dict[int, List[Dict[str, Any]]] = {}

    def get_script_strings(s_idx: int) -> List[Dict[str, Any]]:
        if s_idx not in script_orig_strings:
            rom_off = int(entries[s_idx]["rom_addr"], 16) - GBA_ROM_BASE
            decomp, _ = decompress_gba_lz77(orig_rom, rom_off)
            script_orig_strings[s_idx] = extract_psi3_strings(decomp, specs)
        return script_orig_strings[s_idx]

    translations_by_script: Dict[int, Dict[int, str]] = {}

    for md_path in md_paths:
        current_default_script: Optional[int] = None
        for line in md_path.read_text(encoding="utf-8").splitlines():
            # Detecta cabeçalho de seção com Script #XXXX (suporta múltiplos scripts no título)
            if line.startswith("#"):
                m_sec = re.findall(r"#(\d{4})", line)
                if len(m_sec) >= 1:
                    current_default_script = int(m_sec[0])
                continue

            if not line.startswith("|") or "---" in line or "Texto Original" in line:
                continue

            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 4:
                continue

            col0 = cols[0]
            m_exact = re.search(r"#(\d{4})\s*\[?(\d+)\]?(?!\s*x)", col0)
            if m_exact and "+0x" not in col0:
                s_idx = int(m_exact.group(1))
                str_id = int(m_exact.group(2))
                orig_strs = get_script_strings(s_idx)
                s_trans = translations_by_script.setdefault(s_idx, {})
                pt_lines = extract_backtick_lines(cols[3])
                if pt_lines and str_id < len(orig_strs):
                    combined_pt = "<br>".join(pt_lines)
                    s_trans[str_id] = match_ellipsis_style(orig_strs[str_id]["text"], combined_pt)
                continue

            m_row_script = re.search(r"#(\d{4})", col0)
            s_idx = int(m_row_script.group(1)) if m_row_script else current_default_script
            if s_idx is None:
                continue

            en_lines = extract_backtick_lines(cols[2])
            pt_lines = extract_backtick_lines(cols[3])
            if not en_lines or not pt_lines:
                continue

            orig_strs = get_script_strings(s_idx)
            s_trans = translations_by_script.setdefault(s_idx, {})

            # Faz o pareamento sequencial das linhas em inglês dentro do script
            # normalizando reticências (`…` vs `...`) e espaços finais para matching 100% preciso
            def norm(t: str) -> str:
                return t.replace("…", "...").replace("♡", "☆").strip()

            if len(en_lines) == 1 and len(pt_lines) > 1:
                pairs = [(en_lines[0], "<br>".join(pt_lines))]
            else:
                pairs = list(zip(en_lines, pt_lines))
            search_cursor = 0
            for en_l, pt_l in pairs:
                en_norm = norm(en_l)
                if not en_norm or en_norm == "...":
                    continue
                matched = False
                # Tenta primeiro a partir de search_cursor para preservar a ordem do diálogo
                for pass_num in (0, 1):
                    start_k = search_cursor if pass_num == 0 else 0
                    for k in range(start_k, len(orig_strs)):
                        item = orig_strs[k]
                        if item["string_index"] in s_trans and pass_num == 0:
                            continue
                        if norm(item["text"]) == en_norm:
                            s_trans[item["string_index"]] = match_ellipsis_style(item["text"], pt_l)
                            search_cursor = k + 1
                            matched = True
                            break
                    if matched:
                        break

    return translations_by_script


def main() -> int:
    rom_path = Path("rom/Summon Night - Swordcraft Story (USA).gba")
    out_rom_path = Path("rom/Summon Night - Swordcraft Story (PT-BR).gba")
    pack_json_path = Path("extracted/translation_pack_ptbr.json")
    md_dir = Path("ARQUIVOS md")

    orig_rom = rom_path.read_bytes()
    specs = build_opcode_spec_table(orig_rom)
    entries = parse_archive_table(orig_rom, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)

    print("=" * 88)
    print(f" COMPILADOR UNIFICADO DE ROM PT-BR — SUMMON NIGHT: SWORDCRAFT STORY [AB4E] ({PROJECT_VERSION})")
    print("=" * 88)

    # 1. Injeta a fonte acentuada PT-BR (24 glifos 12x12 1bpp em BIT\0 + tabela 0x081DB270)
    rom_mut = bytearray(inject_ptbr_font_into_rom(orig_rom))
    # Engine patch: remove o limitador artificial de 37 chars em 0x08009E32 (bhi #0x8009e3a -> nop)
    patch_off = 0x08009E32 - GBA_ROM_BASE
    if rom_mut[patch_off : patch_off + 2] == b"\x02\xD8":
        rom_mut[patch_off : patch_off + 2] = b"\xC0\x46"
    print("[1/4] Fonte PT-BR injetada (BIT\\0 + SJIS) e Engine Patch 0x08009E32 aplicado (NOP).")

    # 2. Compila e reponta as strings de UI, Batalha, Forja, Lojas, Link e Save (03-interface...)
    ptr_index = build_rom_pointer_index(orig_rom)
    free_space_cursor = DEFAULT_FREE_SPACE_ADDR - GBA_ROM_BASE
    free_space_cursor, ui_stats = apply_ui_and_system_md(
        rom_mut,
        orig_rom,
        md_dir / "03-interface-menus-batalha-e-sistema.md",
        ptr_index,
        free_space_cursor,
    )
    print(
        f"[2/4] Interface/Menus/Batalha (03): {ui_stats['in_place']} in-place | "
        f"{ui_stats['repointed']} realocadas no espaço livre ({ui_stats['ptrs_updated']} ponteiros 32-bit atualizados)."
    )

    # 3. Compila os catálogos de Armas, Magias, Itens e Bestiário (04, 05, 06, 07)
    cat_stats = apply_catalog_structs_md(rom_mut, md_dir)
    print(
        f"[3/4] Catálogos Estáticos (04..07): {cat_stats['weapons_spells_items']} Armas/Magias/Itens | "
        f"{cat_stats['monsters']} Monstros do Bestiário traduzidos na ROM."
    )

    # 4. Compila todos os scripts de diálogo PSI3 (08, 09 e todos os arquivos .md nas subpastas de Lotes + translation_pack_ptbr.json)
    dialogue_md_files = sorted(
        [
            p for p in md_dir.rglob("*.md")
            if not p.name.startswith(("00-", "01-", "02-", "03-", "04-", "05-", "06-", "07-"))
        ],
        key=lambda p: (p.name, p.as_posix()),
    )
    md_dialogue_trans = parse_dialogue_mds(
        orig_rom,
        specs,
        entries,
        dialogue_md_files,
    )

    # Sincroniza também com extracted/translation_pack_ptbr.json se existir
    if pack_json_path.exists():
        pack_data = json.loads(pack_json_path.read_text(encoding="utf-8"))
        scripts_dict = pack_data.get("scripts", {})
        for s_idx, str_map in md_dialogue_trans.items():
            s_key = str(s_idx)
            if s_key in scripts_dict:
                for item in scripts_dict[s_key]["strings"]:
                    if item["id"] in str_map and str_map[item["id"]]:
                        item["ptbr"] = str_map[item["id"]]
        # Também incorpora quaisquer traduções editadas diretamente no JSON
        for s_key, s_val in scripts_dict.items():
            s_idx = int(s_key)
            for item in s_val["strings"]:
                if item.get("ptbr"):
                    md_dialogue_trans.setdefault(s_idx, {})[item["id"]] = item["ptbr"]
        pack_json_path.write_text(json.dumps(pack_data, indent=2, ensure_ascii=False), encoding="utf-8")

    rebuilt_scripts: Dict[int, bytes] = {}
    total_translated_lines = 0
    for s_idx, str_map in sorted(md_dialogue_trans.items()):
        if not str_map:
            continue
        total_translated_lines += len(str_map)
        rom_off = int(entries[s_idx]["rom_addr"], 16) - GBA_ROM_BASE
        orig_psi3, _ = decompress_gba_lz77(orig_rom, rom_off)
        rebuilt_scripts[s_idx] = rebuild_psi3_script(orig_psi3, specs, translations=str_map)

    # Alinha o cursor de espaço livre em 0x085C10DC + N*16 antes de inserir os scripts LZ77
    next_free_addr = GBA_ROM_BASE + free_space_cursor
    final_rom, reinsert_log = reinsert_scripts_into_rom(
        bytes(rom_mut),
        rebuilt_scripts,
        free_space_start_addr=next_free_addr,
    )

    total_archive_entries = sum(len(item["shared_archive_indices"]) for item in reinsert_log)
    print(
        f"[4/4] Scripts de Diálogo PSI3 (08..09): {len(reinsert_log)} scripts únicos recompilados "
        f"({total_translated_lines} linhas traduzidas, {total_archive_entries} entradas do Archive #2 atualizadas)."
    )

    final_rom_mut = bytearray(final_rom)
    apply_all_menu_patches(final_rom_mut, orig_rom)
    final_rom = bytes(final_rom_mut)

    try:
        out_rom_path.write_bytes(final_rom)
    except OSError:
        # Se a ROM estiver aberta/mapeada em memória pelo emulador (mGBA/VBA),
        # o Windows bloqueia 'wb' (truncate), mas permite 'r+b' sem truncar!
        with out_rom_path.open("r+b") as f:
            f.seek(0)
            f.write(final_rom)
    patch_dir = Path("releases")
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_path = patch_dir / f"Summon Night - Swordcraft Story (PT-BR) {PROJECT_VERSION}.ips"
    patch_size = create_ips_patch(orig_rom, final_rom, patch_path)
    print("-" * 88)
    print(f"[SUCESSO] ROM PT-BR gerada e validada em: {out_rom_path} ({len(final_rom):,} bytes)")
    print(f"[VERSÃO] {PROJECT_VERSION} | Patch IPS gerado em: {patch_path} ({patch_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
