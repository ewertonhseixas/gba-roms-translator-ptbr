#!/usr/bin/env python3
"""
Compilador Central da Tradução PT-BR
Summon Night: Swordcraft Story 2 (USA) [BSKE]
==============================================
Compila:
  1. Tabelas de Interface Estática (00_Interface_Menus_Selecao_e_Sistema.md):
     - Menu inicial, Novo Jogo, Escolha de Personagem, Confirmação de Nome,
       Telas de Sistema, Opções e Salvamento.
  2. Bytecode dos Diálogos PSI3 (01_Prologo... e Lotes 01..18):
     - Introdução em Goura's Gate, diálogos, vilas, eventos e masmorras.
     - Codificação Shift-JIS 16-bit com variáveis {PLAYER}, {PARTNER}, etc.
     - Compressão LZ77 (tipo 0x10) e realocação automática para espaço livre (0x08FCC060+).
  3. Geração do Patch IPS em releases/.
"""

import os
import re
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT_DIR = Path(__file__).resolve().parent.parent
ORIGINAL_ROM = ROOT_DIR / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
OUTPUT_ROM = ROOT_DIR / "rom" / "Summon Night - Swordcraft Story 2 (PT-BR).gba"
RELEASES_DIR = ROOT_DIR / "releases"
MD_DIR = ROOT_DIR / "ARQUIVOS md"

sys.path.insert(0, str(ROOT_DIR / "tools"))
from archive_extractor import decompress_gba_lz77, parse_archive_table
from font_ptbr_injector import PTBR_CHAR_TO_SJIS, inject_ptbr_font_into_rom

GBA_ROM_BASE = 0x08000000
ARCHIVE2_BASE = 0x08ABA81C
ARCHIVE2_LIMIT = 0x08C7F5FC
FREE_SPACE_START = 0x08FCC060

# Mapeamentos de Caracteres
SJIS_PUNCT_ENCODE: Dict[str, int] = {
    " ": 0x8140, ",": 0x8143, ".": 0x8144, "・": 0x8145, ":": 0x8146,
    ";": 0x8147, "?": 0x8148, "!": 0x8149, "-": 0x817C, "/": 0x815E,
    "~": 0x8160, "'": 0x8166, '"': 0x8168, "(": 0x8169, ")": 0x816A,
    "+": 0x817B, "=": 0x8181, "%": 0x8193, "&": 0x8195, "*": 0x8196,
}

WIDE_GLYPH_ENCODE: Dict[str, Tuple[int, int]] = {
    "…": (0x8163, 0x84AD),
    "☆": (0x8199, 0x84AA),
    "★": (0x819A, 0x84AB),
    "◎": (0x819D, 0x84AC),
    "♪": (0x81F4, 0x84AE),
}

VAR_ENCODE: Dict[str, int] = {
    "{PLAYER}": 0x83C0,
    "{PARTNER}": 0x83C1,
    "{VAR_2}": 0x83C2,
    "{SIBLING}": 0x83C3,
    "{VAR_4}": 0x83C4,
    "{MASTER}": 0x83C5,
}

PTBR_ACCENT_FALLBACK: Dict[str, str] = {
    "á": "a", "à": "a", "â": "a", "ã": "a",
    "é": "e", "ê": "e",
    "í": "i",
    "ó": "o", "ô": "o", "õ": "o",
    "ú": "u",
    "ç": "c",
    "Á": "A", "À": "A", "Â": "A", "Ã": "A",
    "É": "E", "Ê": "E",
    "Í": "I",
    "Ó": "O", "Ô": "O", "Õ": "O",
    "Ú": "U",
    "Ç": "C",
}


def encode_sjis_u16(text: str) -> bytes:
    """Codifica string para sequência Big-Endian Shift-JIS de 16-bit com terminador 0x0000."""
    out = bytearray()
    i = 0
    n = len(text)
    while i < n:
        matched_var = False
        for v_tag, v_code in VAR_ENCODE.items():
            if text.startswith(v_tag, i):
                out += struct.pack(">H", v_code)
                i += len(v_tag)
                matched_var = True
                break
        if matched_var:
            continue

        ch = text[i]
        if ch == "@":
            out += struct.pack(">H", 0x8197)
            i += 1
            continue

        # 1. Caracteres acentuados PT-BR suportados pela fonte injetada
        if ch in PTBR_CHAR_TO_SJIS:
            out += struct.pack(">H", PTBR_CHAR_TO_SJIS[ch])
            i += 1
            continue

        ch_norm = PTBR_ACCENT_FALLBACK.get(ch, ch)

        if ch_norm in WIDE_GLYPH_ENCODE:
            w1, w2 = WIDE_GLYPH_ENCODE[ch_norm]
            out += struct.pack(">HH", w1, w2)
        elif "A" <= ch_norm <= "Z":
            out += struct.pack(">H", 0x8260 + ord(ch_norm) - ord("A"))
        elif "a" <= ch_norm <= "z":
            out += struct.pack(">H", 0x8281 + ord(ch_norm) - ord("a"))
        elif "0" <= ch_norm <= "9":
            out += struct.pack(">H", 0x824F + ord(ch_norm) - ord("0"))
        elif ch_norm in SJIS_PUNCT_ENCODE:
            out += struct.pack(">H", SJIS_PUNCT_ENCODE[ch_norm])
        else:
            try:
                b = ch_norm.encode("cp932")
                if len(b) == 2:
                    out += b
                else:
                    out += struct.pack(">H", 0x8140)
            except Exception:
                out += struct.pack(">H", 0x8140)
        i += 1

    out += struct.pack(">H", 0x0000)
    return bytes(out)


def compress_gba_lz77(data: bytes) -> bytes:
    """Comprime dados no formato LZ77 padrão da BIOS do GBA (tipo 0x10)."""
    n = len(data)
    out = bytearray()
    header = 0x10 | (n << 8)
    out += struct.pack("<I", header)

    src = 0
    while src < n:
        flags_pos = len(out)
        out.append(0)
        flags = 0

        for bit in range(7, -1, -1):
            if src >= n:
                break
            best_disp = 0
            best_len = 0
            max_len = min(18, n - src)
            window_start = max(0, src - 4096)

            for cand_disp in range(1, src - window_start + 1):
                match_src = src - cand_disp
                curr_len = 0
                while (curr_len < max_len and
                       data[match_src + (curr_len % cand_disp)] == data[src + curr_len]):
                    curr_len += 1
                if curr_len > best_len:
                    best_len = curr_len
                    best_disp = cand_disp
                    if best_len == max_len:
                        break

            if best_len >= 3:
                flags |= (1 << bit)
                b1 = ((best_len - 3) << 4) | (((best_disp - 1) >> 8) & 0x0F)
                b2 = (best_disp - 1) & 0xFF
                out.extend([b1, b2])
                src += best_len
            else:
                out.append(data[src])
                src += 1

        out[flags_pos] = flags

    pad = (16 - (len(out) % 16)) % 16
    out.extend(b"\x00" * pad)
    return bytes(out)


def create_ips_patch(src: bytes, dst: bytes, out_path: Path) -> int:
    out = bytearray(b"PATCH")
    i = 0
    n = max(len(src), len(dst))
    chunk_size = 4096
    while i < n:
        if i + chunk_size <= n and src[i : i + chunk_size] == dst[i : i + chunk_size]:
            i += chunk_size
            continue
        b_src = src[i] if i < len(src) else None
        b_dst = dst[i] if i < len(dst) else None
        if b_src != b_dst:
            start = i
            diff = bytearray()
            while i < n and len(diff) < 0xFFFF:
                s = src[i] if i < len(src) else None
                d = dst[i] if i < len(dst) else None
                if s == d:
                    ahead = True
                    for k in range(1, 6):
                        if i + k < n:
                            if (src[i+k] if i+k < len(src) else None) != (dst[i+k] if i+k < len(dst) else None):
                                ahead = False
                                break
                    if ahead:
                        break
                diff.append(d)
                i += 1
            out += struct.pack(">I", start)[1:]
            out += struct.pack(">H", len(diff))
            out += diff
        else:
            i += 1
    out += b"EOF"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(out)
    return len(out)


def compile_static_ui(rom: bytearray, free_cursor: int) -> Tuple[int, int, int]:
    """Compila as strings de interface em 00_Interface_Menus_Selecao_e_Sistema.md."""
    ui_md = MD_DIR / "00_Interface_Menus_Selecao_e_Sistema.md"
    if not ui_md.exists():
        return 0, 0, free_cursor

    # Constrói mapa de ponteiros da ROM para a faixa 0x0808E000..0x08095000
    ptr_map = {}
    for off in range(0, len(rom) - 4, 4):
        val = struct.unpack_from("<I", rom, off)[0]
        if 0x0808E000 <= val < 0x08095000:
            if val not in ptr_map:
                ptr_map[val] = []
            ptr_map[val].append(off)

    lines = ui_md.read_text(encoding="utf-8").splitlines()
    in_place = 0
    reloc = 0

    known_addrs = set()
    for line in lines:
        if line.startswith("| `0x"):
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 1:
                try:
                    known_addrs.add(int(cols[0].strip("` "), 16))
                except ValueError:
                    pass

    for line in lines:
        if not line.startswith("| `0x"):
            continue
        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) >= 3 and cols[2]:
            addr_str = cols[0].strip("` ")
            pt_text = cols[2].strip()
            if not pt_text:
                continue

            addr = int(addr_str, 16)
            off = addr - GBA_ROM_BASE

            # Tamanho original da string (incluindo padding de alinhamento até a próxima string)
            p = off
            while p + 1 < len(rom) and struct.unpack_from(">H", rom, p)[0] != 0:
                p += 2
            p += 2  # inclui o terminador nulo 0x0000
            while p + 1 < len(rom) and struct.unpack_from(">H", rom, p)[0] == 0:
                if (GBA_ROM_BASE + p) in known_addrs:
                    break
                p += 2
            orig_len = p - off

            # Preserva prefixo de espaços full-width (0x8140) se houver no original
            leading_spaces = 0
            while off + leading_spaces * 2 + 1 < len(rom) and struct.unpack_from(">H", rom, off + leading_spaces * 2)[0] == 0x8140:
                leading_spaces += 1

            enc = encode_sjis_u16(pt_text)
            if leading_spaces > 0 and not pt_text.startswith(" "):
                enc = (b"\x81\x40" * leading_spaces) + enc

            if len(enc) <= orig_len:
                rom[off : off + orig_len] = enc + b"\x00" * (orig_len - len(enc))
                in_place += 1
            else:
                # Se for maior, ajusta para caber sem corromper ponteiros adjacentes
                max_payload = orig_len - 2
                safe_enc = enc[:max_payload]
                if len(safe_enc) % 2 != 0:
                    safe_enc = safe_enc[:-1]
                safe_enc = safe_enc + b"\x00\x00"
                rom[off : off + orig_len] = safe_enc + b"\x00" * (orig_len - len(safe_enc))
                in_place += 1

    return in_place, reloc, free_cursor


def load_dialogue_translations() -> Dict[int, Dict[int, str]]:
    """Carrega as falas dos lotes de diálogos (01_Prologo e Lote_01..18)."""
    translations: Dict[int, Dict[int, str]] = {}
    if not MD_DIR.exists():
        return translations

    md_files = sorted(MD_DIR.glob("*.md"))
    for md in md_files:
        if md.name.startswith("00_"):
            continue  # Interface já tratada separadamente
        lines = md.read_text(encoding="utf-8").splitlines()
        for line in lines:
            if not line.startswith("| `") or "---" in line or "ID Script" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 5:
                s_id_str = cols[0].strip("` ")
                offset_str = cols[1].strip("` ")
                pt_text = cols[4].strip()
                if pt_text and s_id_str.isdigit():
                    s_id = int(s_id_str)
                    try:
                        off = int(offset_str, 16)
                    except ValueError:
                        continue
                    if s_id not in translations:
                        translations[s_id] = {}
                    translations[s_id][off] = pt_text

    return translations


def fit_sjis_fixed_len(text: str, orig_len: int) -> bytes:
    """
    Codifica o texto para Shift-JIS terminando em 0x0000 de modo que o tamanho
    seja EXATAMENTE orig_len bytes. Se for menor, preenche com espaços full-width 0x8140
    (invisíveis na caixa de diálogo) ANTES do terminador 0x0000.
    Dessa forma, NUNCA adiciona múltiplos 0x0000 (que a VM executaria como opcode nulo)
    e NUNCA altera o tamanho do bytecode (preservando 100% dos offsets de salto da VM).
    """
    enc_chars = bytearray(encode_sjis_u16(text)[:-2])  # remove o 0x0000 final
    max_payload = orig_len - 2

    if len(enc_chars) > max_payload:
        enc_chars = enc_chars[:max_payload]
        if len(enc_chars) % 2 != 0:
            enc_chars = enc_chars[:-1]
    else:
        # Preenche com espaços 0x8140 antes do terminador
        while len(enc_chars) + 2 <= max_payload:
            enc_chars.extend(b"\x81\x40")

    enc_chars.extend(b"\x00\x00")
    while len(enc_chars) < orig_len:
        enc_chars.append(0)

    return bytes(enc_chars)


def apply_translations_to_script(decomp: bytearray, script_trans: Dict[int, str]) -> bytearray:
    for off, new_text in sorted(script_trans.items(), reverse=True):
        if off + 2 >= len(decomp):
            continue
        op = struct.unpack_from("<H", decomp, off)[0]
        if op not in (0x0306, 0x0361, 0x0310, 0x030D):
            continue

        str_start = off + 2
        p = str_start
        while p + 1 < len(decomp) and struct.unpack_from(">H", decomp, p)[0] != 0:
            p += 2
        orig_len = (p + 2) - str_start

        fixed_enc = fit_sjis_fixed_len(new_text, orig_len)
        decomp[str_start : str_start + orig_len] = fixed_enc

    return decomp


def main():
    if not ORIGINAL_ROM.exists():
        print(f"Erro: ROM original não encontrada em {ORIGINAL_ROM}")
        sys.exit(1)

    print("=" * 74)
    print(" COMPILADOR CENTRAL DA TRADUÇÃO PT-BR - SUMMON NIGHT 2 (GBA)")
    print("=" * 74)

    rom = bytearray(ORIGINAL_ROM.read_bytes())
    free_cursor = FREE_SPACE_START - GBA_ROM_BASE

    # 1. Injeção de Fonte Acentuada PT-BR (BIT\0 @ 0x08944D3C + Tabela SJIS @ 0x084C37D4)
    rom = bytearray(inject_ptbr_font_into_rom(rom))
    print("• Fonte PT-BR (BIT\\0)         : 24 glifos acentuados injetados e registrados na tabela SJIS")

    # 2. Compilação da Interface, Menus e Escolha de Personagem
    ui_in_place, ui_reloc, free_cursor = compile_static_ui(rom, free_cursor)
    print(f"• Interface / Menus / Sistema : {ui_in_place + ui_reloc} textos compilados ({ui_in_place} in-place, {ui_reloc} realocados)")

    # 2. Compilação dos Diálogos PSI3 (Prólogo + Lotes)
    translations = load_dialogue_translations()
    total_dialogues = sum(len(v) for v in translations.values())
    print(f"• Diálogos / História (PSI3)  : {total_dialogues} falas carregadas em {len(translations)} scripts.")

    arch2_off = ARCHIVE2_BASE - GBA_ROM_BASE
    entries = parse_archive_table(rom, ARCHIVE2_BASE, ARCHIVE2_LIMIT)

    modified_scripts = 0
    relocated_scripts = 0

    for s_id, trans_map in translations.items():
        if s_id >= len(entries):
            continue
        ent = entries[s_id]
        raw_off = ent["file_offset"]
        raw_sz = ent["compressed_size"]
        raw = rom[raw_off : raw_off + raw_sz]

        if ent["is_lz77"]:
            decomp_res = decompress_gba_lz77(raw)
            if not decomp_res:
                continue
            decomp = bytearray(decomp_res[0])
            mod_decomp = apply_translations_to_script(decomp, trans_map)
            new_comp = compress_gba_lz77(mod_decomp)
        else:
            decomp = bytearray(raw)
            mod_decomp = apply_translations_to_script(decomp, trans_map)
            new_comp = bytes(mod_decomp)

        if len(new_comp) <= raw_sz:
            rom[raw_off : raw_off + len(new_comp)] = new_comp
            if len(new_comp) < raw_sz:
                rom[raw_off + len(new_comp) : raw_off + raw_sz] = b"\x00" * (raw_sz - len(new_comp))
        else:
            # Garante que alloc_off esteja perfeitamente alinhado com arch2_off (módulo 16)
            # Para que (alloc_off - arch2_off) % 16 == 0, sem perder os 4 bits no >> 4!
            rel_cursor = free_cursor - arch2_off
            if rel_cursor % 16 != 0:
                free_cursor += (16 - (rel_cursor % 16))
            alloc_off = free_cursor

            rom[alloc_off : alloc_off + len(new_comp)] = new_comp
            free_cursor += len(new_comp)
            rel_cursor = free_cursor - arch2_off
            if rel_cursor % 16 != 0:
                free_cursor += (16 - (rel_cursor % 16))

            rel_off = alloc_off - arch2_off
            assert rel_off % 16 == 0
            off_u16 = rel_off >> 4
            sz_u16 = (len(new_comp) + 15) >> 4

            idx_off = arch2_off + 8 + s_id * 8
            struct.pack_into("<II", rom, idx_off, off_u16, sz_u16)
            relocated_scripts += 1

        modified_scripts += 1

    # Gravação da ROM traduzida (compatível mesmo se o emulador estiver aberto)
    try:
        tmp_rom = OUTPUT_ROM.with_suffix(".tmp")
        tmp_rom.write_bytes(rom)
        os.replace(tmp_rom, OUTPUT_ROM)
    except Exception:
        try:
            with open(OUTPUT_ROM, "r+b") as f:
                f.seek(0)
                f.write(rom)
                f.truncate()
        except Exception:
            OUTPUT_ROM.write_bytes(rom)
    print(f"\n✅ ROM traduzida compilada com sucesso:")
    print(f"   -> {OUTPUT_ROM.name} ({len(rom) / (1024*1024):.2f} MB)")
    print(f"   -> {modified_scripts} scripts PSI3 reconstruídos ({relocated_scripts} realocados)")

    # Geração do Patch IPS
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    patch_file = RELEASES_DIR / "Summon Night 2 (PT-BR) v0.1.ips"
    ips_size = create_ips_patch(ORIGINAL_ROM.read_bytes(), bytes(rom), patch_file)
    print(f"✅ Patch IPS atualizado em releases/:")
    print(f"   -> {patch_file.name} ({ips_size:,} bytes)")


if __name__ == "__main__":
    main()
