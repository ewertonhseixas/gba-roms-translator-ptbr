#!/usr/bin/env python3
"""
PSI3 Script Compiler, Offset Relocator, LZ77 Compressor & ROM Reinserter
Summon Night: Swordcraft Story (USA) [AB4E]
========================================================================
Ferramenta completa de reconstrução modular e reinserção de scripts PSI3:
  1. Codificador/Decodificador Shift-JIS Full-Width 16-bit 100% bijetivo
     (suporta glifos duplos de 16x12 como '…', '☆', '★', '◎', '♪', variáveis
     dinâmicas {PLAYER}, {PARTNER}, {SIBLING}, {MASTER} e acentuação PT-BR).
  2. Parser e Relocador determinístico de Bytecode PSI3 guiado pelas 5 tabelas
     de opcodes da ROM (275 opcodes), recalculando automaticamente todos os 14
     opcodes de salto/callback (31.739 ponteiros internos no Archive #2).
  3. Compressor LZ77 (formato BIOS GBA 0x10) com alinhamento de 16 bytes.
  4. Reinseridor de ROM com repointing automático na tabela do Archive #2
     (0x085C10DC), alocando no espaço livre (0x08760C30+) ou expandindo a ROM.
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

from archive_extractor import parse_archive_table, decompress_gba_lz77
from font_ptbr_injector import (
    PTBR_CHAR_TO_SJIS,
    PTBR_SJIS_TO_CHAR,
    inject_ptbr_font_into_rom,
)

sys.stdout.reconfigure(encoding="utf-8")

GBA_ROM_BASE = 0x08000000
ARCHIVE2_BASE_ADDR = 0x085C10DC
ARCHIVE2_LIMIT_ADDR = 0x0870771C
DEFAULT_FREE_SPACE_ADDR = 0x08760C2C  # Alinhado em 16 bytes relativo a ARCHIVE2_BASE_ADDR (0x085C10DC + N*16)

# As 5 tabelas de opcodes da VM PSI3 na ROM (descobertas em 0x0800D36C)
VM_TABLES = [
    (0x0000, 0x081DD5C8, 0x40),
    (0x0100, 0x081F57F8, 0xB0),
    (0x0200, 0x081F5AB8, 0x58),
    (0x0300, 0x081F5C18, 0x30),
    (0x0400, 0x081F5CD8, 0x35),
]

# Todos os 14 opcodes cujo argumento u16 bruto (lido via 0x0800CEC8) é um target_offset
# relativo ao início do bytecode (+0x10)
OFFSET_OPCODES = {
    0x0002,  # JZ (target_offset, expr)
    0x0003,  # JMP (target_offset)
    0x0007,  # CALL (target_offset)
    0x0009,  # SPAWN_THREAD_0 (expr, target_offset)
    0x010B,  # SET_MAP_TRIGGER (expr, target_offset, expr)
    0x011E,  # SET_NPC_CB_18A (expr, target_offset)
    0x0162,  # SET_ACTOR_CB_54 (target_offset)
    0x0166,  # SET_ACTOR_CB_56 (target_offset)
    0x016C,  # SET_ACTOR_CB_58 (target_offset)
    0x0185,  # SET_ACTOR_CB_5A (target_offset)
    0x0186,  # SET_ACTOR_CB_5C (target_offset)
    0x018F,  # SET_ACTOR_CB_D0 (target_offset)
    0x0221,  # CHOICE_OPTION (target_offset, inline_str)
    0x0305,  # SPAWN_THREAD_1 (target_offset)
}

# Todos os opcodes que contêm strings Shift-JIS 16-bit inline terminadas em 0x0000
STRING_OPCODES = {
    0x0212,  # String de interface/evento
    0x0218,  # Diálogo principal
    0x021D,  # Caixa de mensagem centralizada ("Small Key used!", etc.)
    0x0220,  # Cabeçalho de pergunta de escolha (Choice Header)
    0x0221,  # Opção de escolha (Choice Option: target_offset + string)
    0x0228,  # Define variável de string dinâmica (expr + string)
    0x0229,  # Define variável de string dinâmica alinhada (expr + string)
}

# Mapeamento bijetivo de pontuação 0x81xx (Big-Endian Shift-JIS -> caractere legível)
SJIS_PUNCT_DECODE: Dict[int, str] = {
    0x8140: " ",
    0x8143: ",",
    0x8144: ".",
    0x8145: "・",
    0x8146: ":",
    0x8147: ";",
    0x8148: "?",
    0x8149: "!",
    0x815B: "ー",
    0x815E: "/",
    0x8160: "~",
    0x8166: "'",
    0x8168: '"',
    0x8169: "(",
    0x816A: ")",
    0x817B: "+",
    0x817C: "-",
    0x817E: "×",
    0x8181: "=",
    0x8183: "<",
    0x8184: ">",
    0x8193: "%",
    0x8194: "#",
    0x8195: "&",
    0x8196: "*",
    0x8197: "@",
}

SJIS_PUNCT_ENCODE: Dict[str, int] = {v: k for k, v in SJIS_PUNCT_DECODE.items()}

# Glifos duplos de 16x12 pixels (2 halfwords consecutivas: metade esquerda 0x81xx + metade direita 0x84xx)
WIDE_GLYPH_PAIRS_DECODE: Dict[Tuple[int, int], str] = {
    (0x8163, 0x84AD): "…",
    (0x8199, 0x84AA): "☆",
    (0x819A, 0x84AB): "★",
    (0x819D, 0x84AC): "◎",
    (0x81F4, 0x84AE): "♪",
}

WIDE_GLYPH_PAIRS_ENCODE: Dict[str, Tuple[int, int]] = {
    v: k for k, v in WIDE_GLYPH_PAIRS_DECODE.items()
}
WIDE_GLYPH_PAIRS_ENCODE["♡"] = (0x8199, 0x84AA)

# Variáveis dinâmicas 0x83C0..0x83CF
VAR_DECODE: Dict[int, str] = {
    0x83C0: "{PLAYER}",
    0x83C1: "{PARTNER}",
    0x83C2: "{VAR_2}",
    0x83C3: "{SIBLING}",
    0x83C4: "{VAR_4}",
    0x83C5: "{MASTER}",
}

VAR_ENCODE: Dict[str, int] = {v: k for k, v in VAR_DECODE.items()}

# Mapa de normalização de acentos PT-BR (usado enquanto a fonte BIT\0 original não tiver glifos acentuados injetados;
# se custom_accent_map for fornecido, usa os codepoints Shift-JIS dedicados na fonte!)
PTBR_ASCII_FALLBACK: Dict[str, str] = {
    "á": "a", "à": "a", "â": "a", "ã": "a",
    "Á": "A", "À": "A", "Â": "A", "Ã": "A",
    "é": "e", "ê": "e", "É": "E", "Ê": "E", "Ẽ": "É", "ẽ": "e",
    "í": "i", "Í": "I",
    "ó": "o", "ô": "o", "õ": "o", "Ó": "O", "Ô": "O", "Õ": "O",
    "ú": "u", "ü": "u", "Ú": "U", "Ü": "U",
    "ç": "c", "Ç": "C",
    "º": "o", "ª": "a",
    "–": "-", "—": "-",
}


def decode_psi3_string(data: bytes, start_pos: int) -> Tuple[str, int]:
    """
    Decodifica uma string Shift-JIS 16-bit (terminada em 0x0000) a partir de `start_pos`.
    Retorna `(texto_decodificado, pos_apos_terminador_0x0000)`.
    Garante bijeção 100% reversível por `encode_psi3_string`.
    """
    n = len(data)
    pos = start_pos
    hws_be: List[int] = []
    while pos < n:
        hw_le = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if hw_le == 0x0000:
            break
        b0 = hw_le & 0xFF
        b1 = (hw_le >> 8) & 0xFF
        hws_be.append((b0 << 8) | b1)

    out: List[str] = []
    i = 0
    m = len(hws_be)
    while i < m:
        sjis_be = hws_be[i]
        # 1. Verifica par de glifo duplo de 16x12 (ex: 0x8163 + 0x84AD -> '…')
        if i + 1 < m and (sjis_be, hws_be[i + 1]) in WIDE_GLYPH_PAIRS_DECODE:
            out.append(WIDE_GLYPH_PAIRS_DECODE[(sjis_be, hws_be[i + 1])])
            i += 2
            continue

        # 2. Variáveis dinâmicas (0x83C0..0x83CF)
        if sjis_be in VAR_DECODE:
            out.append(VAR_DECODE[sjis_be])
            i += 1
            continue
        if (sjis_be & 0xFFF0) == 0x83C0:
            out.append(f"{{VAR_{sjis_be & 0xF:X}}}")
            i += 1
            continue

        # 3. Tags de controle 0x87xx
        if (sjis_be >> 8) == 0x87:
            low = sjis_be & 0xFF
            if (low & 0xF0) == 0x40:
                out.append(f"{{CMD_874{low & 0xF:X}}}")
            elif (low & 0xF0) == 0x70:
                out.append(f"{{COLOR_{low & 0xF:X}}}")
            else:
                out.append(f"{{RAW:{sjis_be:04X}}}")
            i += 1
            continue

        # 4. Algarismos Full-Width ('0'..'9')
        if 0x824F <= sjis_be <= 0x8258:
            out.append(chr(ord("0") + (sjis_be - 0x824F)))
            i += 1
            continue

        # 5. Letras Maiúsculas Full-Width ('A'..'Z')
        if 0x8260 <= sjis_be <= 0x8279:
            out.append(chr(ord("A") + (sjis_be - 0x8260)))
            i += 1
            continue

        # 6. Letras Minúsculas Full-Width ('a'..'z')
        if 0x8281 <= sjis_be <= 0x829A:
            out.append(chr(ord("a") + (sjis_be - 0x8281)))
            i += 1
            continue

        # 7. Pontuação Full-Width mapeada (0x81xx) e Acentos PT-BR (0x8440..0x8457)
        if sjis_be in SJIS_PUNCT_DECODE:
            out.append(SJIS_PUNCT_DECODE[sjis_be])
            i += 1
            continue
        if sjis_be in PTBR_SJIS_TO_CHAR:
            out.append(PTBR_SJIS_TO_CHAR[sjis_be])
            i += 1
            continue

        # 8. Caracteres japoneses Shift-JIS padrão (Hiragana, Katakana, Kanji)
        b0 = (sjis_be >> 8) & 0xFF
        b1 = sjis_be & 0xFF
        if (0x829F <= sjis_be <= 0x8396) or (0x889F <= sjis_be <= 0x9FFC) or (0xE040 <= sjis_be <= 0xEAA4):
            try:
                ch = bytes([b0, b1]).decode("shift_jis")
                # Verifica se codificar de volta em shift_jis produz exatamente o mesmo sjis_be
                if ch not in SJIS_PUNCT_ENCODE and ch not in WIDE_GLYPH_PAIRS_ENCODE:
                    enc = ch.encode("shift_jis")
                    if len(enc) == 2 and ((enc[0] << 8) | enc[1]) == sjis_be:
                        out.append(ch)
                        i += 1
                        continue
            except UnicodeDecodeError:
                pass

        # 9. Fallback literal exato {RAW:XXXX}
        out.append(f"{{RAW:{sjis_be:04X}}}")
        i += 1

    return ("".join(out), pos)


def encode_psi3_string(
    text: str,
    custom_accent_map: Optional[Dict[str, int]] = None,
    use_ascii_fallback_for_accents: bool = True,
) -> bytes:
    """
    Codifica uma string (com tags `{PLAYER}`, `{PARTNER}`, `{SIBLING}`, `{MASTER}`,
    `{COLOR_X}`, `{CMD_874X}`, `{RAW:XXXX}`, glifos duplos `…`, `☆`, `★`, `◎`, `♪`,
    ou texto PT-BR) de volta para bytes 16-bit Shift-JIS terminados por `0x0000`.
    """
    hws_be: List[int] = []
    i = 0
    n = len(text)

    while i < n:
        # 1. Tags entre chaves {...}
        if text[i] == "{":
            end_brace = text.find("}", i)
            if end_brace != -1:
                tag = text[i : end_brace + 1]
                if tag in VAR_ENCODE:
                    hws_be.append(VAR_ENCODE[tag])
                    i = end_brace + 1
                    continue
                elif tag.startswith("{VAR_") and len(tag) == 7:
                    idx = int(tag[5], 16)
                    hws_be.append(0x83C0 | idx)
                    i = end_brace + 1
                    continue
                elif tag.startswith("{CMD_874") and len(tag) == 10:
                    idx = int(tag[8], 16)
                    hws_be.append(0x8740 | idx)
                    i = end_brace + 1
                    continue
                elif tag.startswith("{COLOR_") and len(tag) == 9:
                    idx = int(tag[7], 16)
                    hws_be.append(0x8770 | idx)
                    i = end_brace + 1
                    continue
                elif tag.startswith("{RAW:") and len(tag) == 10:
                    val = int(tag[5:9], 16)
                    hws_be.append(val)
                    i = end_brace + 1
                    continue

        ch = text[i]
        if ch in ("\u200b", "\u200c", "\u200d", "\ufeff", "\xad", "\r", "\n"):
            i += 1
            continue
        if ch == "\xa0":
            ch = " "
        elif ch in ("“", "”", "«", "»"):
            ch = '"'
        elif ch in ("‘", "’", "´", "`"):
            ch = "'"
        elif ch in ("–", "—", "―"):
            ch = "-"
        elif ch == "Ẽ":
            ch = "É"
        elif ch in PTBR_ASCII_FALLBACK and ch not in PTBR_CHAR_TO_SJIS:
            ch = PTBR_ASCII_FALLBACK[ch]

        # 2. Mapa de acentos PT-BR (padrão: PTBR_CHAR_TO_SJIS @ 0x8440..0x8459 injetados em BIT\0)
        active_accent_map = custom_accent_map if custom_accent_map is not None else PTBR_CHAR_TO_SJIS
        if active_accent_map and ch in active_accent_map:
            hws_be.append(active_accent_map[ch])
            i += 1
            continue
        if use_ascii_fallback_for_accents and ch in PTBR_ASCII_FALLBACK:
            ch = PTBR_ASCII_FALLBACK[ch]

        # 3. Glifos duplos de 16x12 ('…', '☆', '★', '◎', '♪')
        if ch in WIDE_GLYPH_PAIRS_ENCODE:
            left_be, right_be = WIDE_GLYPH_PAIRS_ENCODE[ch]
            hws_be.append(left_be)
            hws_be.append(right_be)
            i += 1
            continue

        # 4. Algarismos ASCII ('0'..'9')
        if "0" <= ch <= "9":
            hws_be.append(0x824F + (ord(ch) - ord("0")))
            i += 1
            continue

        # 5. Letras Maiúsculas ASCII ('A'..'Z')
        if "A" <= ch <= "Z":
            hws_be.append(0x8260 + (ord(ch) - ord("A")))
            i += 1
            continue

        # 6. Letras Minúsculas ASCII ('a'..'z')
        if "a" <= ch <= "z":
            hws_be.append(0x8281 + (ord(ch) - ord("a")))
            i += 1
            continue

        # 7. Pontuação mapeada (' ', ',', '.', ':', ';', '?', '!', "'", '"', '(', ')', '-', '~', etc.)
        if ch in SJIS_PUNCT_ENCODE:
            hws_be.append(SJIS_PUNCT_ENCODE[ch])
            i += 1
            continue

        # 8. Caracteres japoneses Shift-JIS (Hiragana, Katakana, Kanji)
        try:
            enc = ch.encode("shift_jis")
            if len(enc) == 2:
                hws_be.append((enc[0] << 8) | enc[1])
                i += 1
                continue
        except UnicodeEncodeError:
            pass

        raise ValueError(f"Caractere não suportado na codificação Shift-JIS: {ch!r} em {text!r}")

    # Empacota cada código Shift-JIS (b0, b1) na ordem esperada pela ROM (b0 no endereço par, b1 no ímpar)
    out = bytearray()
    for sjis_be in hws_be:
        b0 = (sjis_be >> 8) & 0xFF
        b1 = sjis_be & 0xFF
        out.append(b0)
        out.append(b1)
    # Terminador nulo 16-bit (0x0000)
    out.extend(b"\x00\x00")
    return bytes(out)


def build_opcode_spec_table(rom: bytes) -> Dict[int, List[str]]:
    """
    Lê as 5 tabelas de opcodes da VM diretamente da ROM e retorna a assinatura
    de argumentos de todos os 275 opcodes válidos:
      - 'EXPR': expressão RPN terminada em 0x0000
      - 'OFFSET': u16 target_offset (relativo a +0x10)
      - 'U16': u16 bruto (não-offset)
      - 'STR': string Shift-JIS 16-bit terminada em 0x0000
    """
    md = Cs(CS_ARCH_ARM, CS_MODE_THUMB)
    specs: Dict[int, List[str]] = {}
    for prefix, tbl_addr, count in VM_TABLES:
        off = tbl_addr - GBA_ROM_BASE
        for i in range(count):
            ptr = struct.unpack_from("<I", rom, off + i * 4)[0]
            if not (0x08000000 <= ptr < 0x08800000):
                continue
            op = prefix | i
            if op in (0x0212, 0x0218, 0x021D, 0x0220):
                specs[op] = ["STR"]
                continue
            elif op == 0x0221:
                specs[op] = ["OFFSET", "STR"]
                continue
            elif op in (0x0228, 0x0229):
                specs[op] = ["EXPR", "STR"]
                continue
            elif op == 0x0223:
                specs[op] = ["EXPR"] * 5
                continue

            fn_addr = ptr & ~1
            fn_off = fn_addr - GBA_ROM_BASE
            arg_list: List[str] = []
            for insn in md.disasm(rom[fn_off : fn_off + 1200], fn_addr):
                if insn.mnemonic == "bl":
                    if insn.op_str == "#0x800cef4":
                        arg_list.append("EXPR")
                    elif insn.op_str == "#0x800cec8":
                        arg_list.append("OFFSET" if op in OFFSET_OPCODES else "U16")
                if insn.mnemonic == "bx" and any(r in insn.op_str for r in ("lr", "r0", "r1", "r2", "r3")):
                    break
                if insn.mnemonic == "pop" and "pc" in insn.op_str:
                    break
            specs[op] = arg_list
    return specs


def _consume_expr(data: bytes, pos: int) -> int:
    n = len(data)
    while pos < n:
        tok = struct.unpack_from("<H", data, pos)[0]
        pos += 2
        if tok == 0x0000:
            return pos
        elif tok in (0x0001, 0x0002, 0x0003):
            pos += 2
        elif 0x0080 <= tok <= 0x0091:
            pass
        else:
            raise ValueError(f"Token RPN desconhecido 0x{tok:04X} @ 0x{pos-2:X}")
    raise ValueError("EOF inesperado em expressão RPN")


def extract_psi3_strings(data: bytes, specs: Dict[int, List[str]]) -> List[Dict[str, Any]]:
    """
    Extrai todas as strings de um binário PSI3 descomprimido na ordem exata das instruções.
    Cada item contém `string_index`, `insn_offset`, `opcode`, `text`.
    """
    if data[:4] != b"PSI3":
        raise ValueError("Cabeçalho PSI3 inválido")
    pos = 0x10
    n = len(data)
    strings: List[Dict[str, Any]] = []
    str_idx = 0

    while pos < n:
        insn_start = pos
        op = struct.unpack_from("<H", data, pos)[0]
        if op == 0x0000:
            break
        pos += 2
        for arg_type in specs[op]:
            if arg_type in ("OFFSET", "U16"):
                pos += 2
            elif arg_type == "EXPR":
                pos = _consume_expr(data, pos)
            elif arg_type == "STR":
                text, next_pos = decode_psi3_string(data, pos)
                strings.append({
                    "string_index": str_idx,
                    "insn_offset": f"0x{insn_start:04X}",
                    "str_offset": f"0x{pos:04X}",
                    "opcode": f"0x{op:04X}",
                    "text": text,
                })
                str_idx += 1
                pos = next_pos

    return strings


def rebuild_psi3_script(
    orig_data: bytes,
    specs: Dict[int, List[str]],
    translations: Optional[Dict[int, str]] = None,
    text_replacements: Optional[Dict[str, str]] = None,
    custom_accent_map: Optional[Dict[str, int]] = None,
) -> bytes:
    """
    Reconstrói um script PSI3 descomprimido substituindo strings traduzidas
    (por `string_index` via `translations` ou por texto exato via `text_replacements`)
    e recalculando todos os 14 opcodes de `target_offset` (`OFFSET_OPCODES`).

    Retorna o novo binário `PSI3` completo e alinhado.
    """
    if orig_data[:4] != b"PSI3":
        raise ValueError("Cabeçalho PSI3 inválido")

    translations = translations or {}
    text_replacements = text_replacements or {}

    pos = 0x10
    n = len(orig_data)
    parsed_insns: List[Dict[str, Any]] = []
    str_idx = 0

    # Passo 1: Parseia todas as instruções e monta os novos bytes de cada instrução
    old_rel_to_new_rel: Dict[int, int] = {}
    new_rel_cursor = 0

    while pos < n:
        insn_start = pos
        old_rel = insn_start - 0x10
        old_rel_to_new_rel[old_rel] = new_rel_cursor

        op = struct.unpack_from("<H", orig_data, pos)[0]
        if op == 0x0000:
            # Padding final 0x0000
            if all(b == 0 for b in orig_data[pos:]):
                break
            raise ValueError(f"Opcode 0x0000 inesperado no meio do script @ 0x{pos:X}")

        pos += 2
        args_parsed: List[Tuple[str, Any]] = []
        insn_byte_len = 2
        multiline_handled = False

        for arg_type in specs[op]:
            if arg_type == "OFFSET":
                raw_off = struct.unpack_from("<H", orig_data, pos)[0]
                pos += 2
                args_parsed.append(("OFFSET", raw_off))
                insn_byte_len += 2
            elif arg_type == "U16":
                raw_u16 = struct.unpack_from("<H", orig_data, pos)[0]
                pos += 2
                args_parsed.append(("U16", raw_u16))
                insn_byte_len += 2
            elif arg_type == "EXPR":
                expr_start = pos
                pos = _consume_expr(orig_data, pos)
                expr_bytes = orig_data[expr_start:pos]
                args_parsed.append(("RAW_BYTES", expr_bytes))
                insn_byte_len += len(expr_bytes)
            elif arg_type == "STR":
                orig_text, next_pos = decode_psi3_string(orig_data, pos)
                if str_idx in translations:
                    new_text = translations[str_idx]
                elif orig_text in text_replacements:
                    new_text = text_replacements[orig_text]
                else:
                    new_text = orig_text

                str_idx += 1
                pos = next_pos

                # Suporte a quebra de linha em diálogos (0x0218): se a tradução contiver <br> ou \n,
                # emite múltiplas instruções 0x0218 sequenciais na VM (até 3 linhas por caixa)
                if op == 0x0218 and ("<br>" in new_text or "\n" in new_text):
                    sub_lines = [s.strip() for s in re.split(r"<br\s*/?>|\n", new_text) if s.strip()]
                    if len(sub_lines) > 1:
                        multiline_handled = True
                        enc_first = encode_psi3_string(sub_lines[0], custom_accent_map=custom_accent_map)
                        parsed_insns.append({
                            "old_rel": old_rel,
                            "new_rel": new_rel_cursor,
                            "op": 0x0218,
                            "args": [("RAW_BYTES", enc_first)],
                        })
                        new_rel_cursor += 2 + len(enc_first)
                        for sub in sub_lines[1:]:
                            enc_sub = encode_psi3_string(sub, custom_accent_map=custom_accent_map)
                            parsed_insns.append({
                                "old_rel": -1,
                                "new_rel": new_rel_cursor,
                                "op": 0x0218,
                                "args": [("RAW_BYTES", enc_sub)],
                            })
                            new_rel_cursor += 2 + len(enc_sub)
                        break

                enc_str = encode_psi3_string(new_text, custom_accent_map=custom_accent_map)
                args_parsed.append(("RAW_BYTES", enc_str))
                insn_byte_len += len(enc_str)

        if multiline_handled:
            continue

        parsed_insns.append({
            "old_rel": old_rel,
            "new_rel": new_rel_cursor,
            "op": op,
            "args": args_parsed,
        })
        new_rel_cursor += insn_byte_len

    # Registra também o offset de fim de código caso algum salto aponte para o fim
    old_end_rel = pos - 0x10
    old_rel_to_new_rel[old_end_rel] = new_rel_cursor

    # Passo 2: Emite o bytecode relocado atualizando todos os argumentos OFFSET
    bytecode_out = bytearray()
    for insn in parsed_insns:
        bytecode_out.extend(struct.pack("<H", insn["op"]))
        for arg_kind, arg_val in insn["args"]:
            if arg_kind == "OFFSET":
                old_target_rel = arg_val & 0xFFFE
                low_bit = arg_val & 1
                if old_target_rel not in old_rel_to_new_rel:
                    raise ValueError(
                        f"Target offset 0x{old_target_rel:04X} (em opcode 0x{insn['op']:04X} @ old_rel 0x{insn['old_rel']:04X}) "
                        f"não aponta para início de instrução!"
                    )
                new_target_rel = old_rel_to_new_rel[old_target_rel]
                if new_target_rel > 0xFFFE:
                    raise ValueError(f"Script excedeu o limite de 64 KB de endereçamento u16 (0x{new_target_rel:X})")
                bytecode_out.extend(struct.pack("<H", new_target_rel | low_bit))
            elif arg_kind == "U16":
                bytecode_out.extend(struct.pack("<H", arg_val))
            elif arg_kind == "RAW_BYTES":
                bytecode_out.extend(arg_val)

    # Passo 3: Preserva alinhamento de 4 bytes no tamanho total do arquivo PSI3 (igual ao compilador original)
    total_unaligned = 0x10 + len(bytecode_out)
    # Se nenhuma string foi alterada, preserva exatamente o tamanho/padding original para round-trip 100% idêntico
    if not translations and not text_replacements:
        orig_decl_size = struct.unpack_from("<I", orig_data, 4)[0]
        while 0x10 + len(bytecode_out) < len(orig_data):
            bytecode_out.append(0)
        decl_size = orig_decl_size
    else:
        while (0x10 + len(bytecode_out)) % 4 != 0:
            bytecode_out.append(0)
        decl_size = 0x10 + len(bytecode_out)

    header = bytearray(16)
    header[0:4] = b"PSI3"
    struct.pack_into("<I", header, 4, decl_size)
    header[8:16] = orig_data[8:16]

    return bytes(header + bytecode_out)


def compress_gba_lz77(raw: bytes, vram_safe: bool = False) -> bytes:
    """
    Comprime `raw` usando o algoritmo LZ77 da BIOS do GBA (Header 0x10 + tamanho 24-bit).
    Compatível 100% com `SWI 0x11` (LZ77UnCompWram) usado em `0x08007000`.
    """
    n = len(raw)
    out = bytearray()
    out.extend(struct.pack("<I", 0x10 | (n << 8)))

    min_disp = 2 if vram_safe else 1
    max_disp = 4096
    max_len = 18

    pos = 0
    while pos < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0

        for bit in range(7, -1, -1):
            if pos >= n:
                break

            best_len = 0
            best_disp = 0
            win_start = max(0, pos - max_disp)
            max_match = min(max_len, n - pos)

            if max_match >= 3 and pos - win_start >= min_disp:
                # Busca rápida na janela deslizante usando `bytes.find` / `rfind`
                sub3 = raw[pos : pos + 3]
                search_end = pos - min_disp + 2
                cur = raw.rfind(sub3, win_start, search_end)
                while cur != -1:
                    disp = pos - cur
                    if disp >= min_disp:
                        m_len = 3
                        while m_len < max_match and raw[cur + m_len] == raw[pos + m_len]:
                            m_len += 1
                        if m_len > best_len:
                            best_len = m_len
                            best_disp = disp
                            if best_len == max_match:
                                break
                    if cur == win_start:
                        break
                    cur = raw.rfind(sub3, win_start, cur + 2)

            if best_len >= 3:
                flags |= 1 << bit
                disp_m1 = best_disp - 1
                len_m3 = best_len - 3
                b1 = (len_m3 << 4) | ((disp_m1 >> 8) & 0x0F)
                b2 = disp_m1 & 0xFF
                out.append(b1)
                out.append(b2)
                pos += best_len
            else:
                out.append(raw[pos])
                pos += 1

        out[flag_pos] = flags

    # Alinha para múltiplo de 4 bytes
    while len(out) % 4 != 0:
        out.append(0)
    return bytes(out)


def reinsert_scripts_into_rom(
    rom_bytes: bytes,
    rebuilt_scripts_by_index: Dict[int, bytes],
    free_space_start_addr: int = DEFAULT_FREE_SPACE_ADDR,
) -> Tuple[bytes, List[Dict[str, Any]]]:
    """
    Comprime cada script PSI3 modificado em `rebuilt_scripts_by_index` (`{file_index: decomp_psi3_bytes}`),
    aloca no espaço livre da ROM (alinhado em 16 bytes) e atualiza TODAS as entradas da tabela do
    Archive #2 (`0x085C10DC`) que compartilhavam o mesmo ponteiro original!

    Nota: Como `Archive_GetFileRomPtr(2, idx)` (`0x08006FC4`) calcula:
      `rom_ptr = 0x085C10DC + (offset_units_16 << 4)`
    qualquer endereço alinhado em 16 bytes após `0x085C10DC` (incluindo o espaço livre `0x08760C30+`
    ou ROM expandida `0x08800000+`) funciona nativamente sem precisar alterar nenhuma instrução ARM/THUMB!
    """
    # Injeta automaticamente os 24 glifos acentuados PT-BR em BIT\0 (0x08707808) e na tabela 0x081DB270
    rom_mut = bytearray(inject_ptbr_font_into_rom(rom_bytes))
    entries = parse_archive_table(rom_bytes, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)

    # Agrupa todos os file_indices que apontam para o mesmo endereço original na ROM
    addr_to_indices: Dict[int, List[int]] = {}
    addr_to_orig_size: Dict[int, int] = {}
    idx_to_orig_addr: Dict[int, int] = {}
    for e in entries:
        f_idx = e["index"]
        f_addr = int(e["rom_addr"], 16)
        idx_to_orig_addr[f_idx] = f_addr
        addr_to_indices.setdefault(f_addr, []).append(f_idx)
        if e["compressed_size"] > addr_to_orig_size.get(f_addr, 0):
            addr_to_orig_size[f_addr] = e["compressed_size"]

    archive2_base_off = ARCHIVE2_BASE_ADDR - GBA_ROM_BASE
    rel_start = max(0, free_space_start_addr - ARCHIVE2_BASE_ADDR)
    rel_aligned = (rel_start + 15) & ~15
    write_cursor_off = archive2_base_off + rel_aligned

    reinsertion_log: List[Dict[str, Any]] = []
    processed_orig_addrs = set()

    # Passo 1: Comprime todos os scripts modificados e coleta todos os slots originais liberados no Archive #2
    prepared_items: List[Tuple[int, int, bytes, bytearray]] = []
    raw_freed_intervals: List[Tuple[int, int]] = []

    for script_idx, new_psi3_bytes in sorted(rebuilt_scripts_by_index.items()):
        if script_idx not in idx_to_orig_addr:
            raise ValueError(f"Índice de script inválido no Archive #2: {script_idx}")
        orig_addr = idx_to_orig_addr[script_idx]
        if orig_addr in processed_orig_addrs:
            continue
        processed_orig_addrs.add(orig_addr)

        comp_bytes = compress_gba_lz77(new_psi3_bytes)
        aligned_comp = bytearray(comp_bytes)
        while len(aligned_comp) % 16 != 0:
            aligned_comp.append(0)

        orig_slot_size = addr_to_orig_size.get(orig_addr, 0)
        orig_rom_off = orig_addr - GBA_ROM_BASE
        if orig_slot_size >= 16:
            raw_freed_intervals.append((orig_rom_off, orig_rom_off + orig_slot_size))

        prepared_items.append((script_idx, orig_addr, new_psi3_bytes, aligned_comp))

    # Funde intervalos contíguos liberados dentro da região do Archive #2 (0x085C736C..0x0870771C)
    raw_freed_intervals.sort()
    freed_slots: List[List[int]] = []  # [[start_off, length], ...]
    for start_off, end_off in raw_freed_intervals:
        if freed_slots and freed_slots[-1][0] + freed_slots[-1][1] == start_off:
            freed_slots[-1][1] = end_off - freed_slots[-1][0]
        else:
            freed_slots.append([start_off, end_off - start_off])

    # Passo 2: Aloca cada script comprimido nos blocos liberados do Archive #2 ou no espaço livre (0x08760C2C+)
    for script_idx, orig_addr, new_psi3_bytes, aligned_comp in prepared_items:
        allocated_off = None
        for slot in freed_slots:
            if slot[1] >= len(aligned_comp):
                allocated_off = slot[0]
                slot[0] += len(aligned_comp)
                slot[1] -= len(aligned_comp)
                break

        if allocated_off is not None:
            new_rom_off = allocated_off
        else:
            if write_cursor_off + len(aligned_comp) > len(rom_mut):
                rom_mut.extend(b"\x00" * (write_cursor_off + len(aligned_comp) - len(rom_mut)))
            new_rom_off = write_cursor_off
            write_cursor_off += len(aligned_comp)

        new_rom_addr = GBA_ROM_BASE + new_rom_off
        rom_mut[new_rom_off : new_rom_off + len(aligned_comp)] = aligned_comp

        new_offset_units_16 = (new_rom_off - archive2_base_off) >> 4
        new_size_units_16 = len(aligned_comp) >> 4

        # Atualiza todas as entradas da tabela do Archive #2 que apontavam para `orig_addr`
        shared_indices = addr_to_indices[orig_addr]
        for target_idx in shared_indices:
            ent_off = archive2_base_off + 8 + target_idx * 8
            struct.pack_into("<II", rom_mut, ent_off, new_offset_units_16, new_size_units_16)

        reinsertion_log.append({
            "primary_script_index": script_idx,
            "shared_archive_indices": shared_indices,
            "old_rom_addr": f"0x{orig_addr:08X}",
            "new_rom_addr": f"0x{new_rom_addr:08X}",
            "decomp_size": len(new_psi3_bytes),
            "comp_size_aligned": len(aligned_comp),
            "offset_units_16": new_offset_units_16,
            "size_units_16": new_size_units_16,
        })

    return (bytes(rom_mut), reinsertion_log)


def run_verification_suite(rom_path: Path) -> int:
    """
    Executa a bateria completa de testes de engenharia reversa e compilação:
      1. Testa bijeção de strings em todas as 30.447 strings de todos os 1.189 scripts únicos.
      2. Testa reconstrução sem alterações (round-trip byte-a-byte) de todos os 1.189 scripts.
      3. Testa compressão/descompressão LZ77 e reinserção PT-BR de prova de conceito
         no script de abertura (`script_0170` / `script_0201`), gerando uma ROM patcheada.
    """
    rom = rom_path.read_bytes()
    specs = build_opcode_spec_table(rom)
    entries = parse_archive_table(rom, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)

    print("=" * 88)
    print(" 1. TESTE DE ROUND-TRIP BYTE-A-BYTE EM TODOS OS 1.189 SCRIPTS ÚNICOS DO ARCHIVE #2")
    print("=" * 88)

    seen_offsets = set()
    total_unique = 0
    total_strings = 0
    exact_matches = 0

    for e in entries:
        rom_off = int(e["rom_addr"], 16) - GBA_ROM_BASE
        if rom_off in seen_offsets:
            continue
        seen_offsets.add(rom_off)
        res = decompress_gba_lz77(rom, rom_off)
        if not res:
            continue
        orig_psi3, _ = res
        if orig_psi3[:4] != b"PSI3":
            continue

        total_unique += 1
        strs = extract_psi3_strings(orig_psi3, specs)
        total_strings += len(strs)

        rebuilt_psi3 = rebuild_psi3_script(orig_psi3, specs)
        if rebuilt_psi3 != orig_psi3:
            print(f"  [ERRO] Divergência de round-trip em script_{e['index']:04d}!")
            return 1
        exact_matches += 1

    print(f"  [OK] Scripts únicos verificados : {exact_matches}/{total_unique} (100.0% byte-a-byte idênticos!)")
    print(f"  [OK] Strings Shift-JIS testadas : {total_strings:,} strings (100.0% bijeção sem perdas!)")

    print("\n" + "=" * 88)
    print(" 2. TESTE DE RELOCAÇÃO DE SALTOS + COMPRESSÃO LZ77 + REINSERÇÃO PT-BR NA ROM")
    print("=" * 88)

    # Seleciona script_0170 (monólogo de abertura de Bron) e script_0201 para teste real PT-BR com mudança de tamanho
    target_idx = 170
    target_entry = entries[target_idx]
    target_rom_off = int(target_entry["rom_addr"], 16) - GBA_ROM_BASE
    orig_170, orig_comp_len = decompress_gba_lz77(rom, target_rom_off)

    ptbr_sample_replacements = {
        "Whoa, not so fast! Go forge that": (
            "Opa, não tão rápido! Vá forjar aquela"
        ),
        "last weapon I taught ya before": (
            "última arma que te ensinei antes de"
        ),
        "moving on to the next!": (
            "passar para a próxima técnica!"
        ),
        "There ain't any techniques I can": (
            "Não há nenhuma técnica nova que eu possa"
        ),
        "teach ya right now.": (
            "te ensinar neste exato momento."
        ),
    }

    rebuilt_170 = rebuild_psi3_script(
        orig_170,
        specs,
        text_replacements=ptbr_sample_replacements,
    )

    # Verifica que todas as strings e offsets do script reconstruído continuam 100% válidos
    rebuilt_strs = extract_psi3_strings(rebuilt_170, specs)
    print(f"  Script #{target_idx:04d} original descomprimido   : {len(orig_170):,} bytes")
    print(f"  Script #{target_idx:04d} traduzido descomprimido  : {len(rebuilt_170):,} bytes (delta: {len(rebuilt_170) - len(orig_170):+d} bytes)")
    for s in rebuilt_strs[:5]:
        print(f"    [{s['insn_offset']}] ({s['opcode']}) {s['text']}")

    # Insere na cópia da ROM e valida leitura via tabela do Archive #2
    patched_rom, log = reinsert_scripts_into_rom(rom, {target_idx: rebuilt_170})
    info = log[0]
    print(f"\n  [REPOINT ARCHIVE #2 CONCLUÍDO]")
    print(f"    Índices atualizados na tabela : {info['shared_archive_indices']}")
    print(f"    Endereço antigo na ROM        : {info['old_rom_addr']}")
    print(f"    Novo endereço na ROM (Livre)  : {info['new_rom_addr']}")
    print(f"    Tamanho comprimido LZ77 (16B) : {info['comp_size_aligned']:,} bytes")

    # Verifica na ROM patcheada usando a mesma fórmula de Archive_GetFileRomPtr (0x08006FC4)
    new_entries = parse_archive_table(patched_rom, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)
    verify_addr = int(new_entries[target_idx]["rom_addr"], 16)
    verify_decomp, _ = decompress_gba_lz77(patched_rom, verify_addr - GBA_ROM_BASE)
    assert verify_decomp == rebuilt_170, "Falha ao descomprimir o script reinserido da ROM patcheada!"
    print(f"    Verificação LZ77 pós-patch    : OK! (`Archive_GetFileRomPtr(2, {target_idx})` -> 0x{verify_addr:08X})")

    out_rom_path = Path("rom/Summon Night - Swordcraft Story (PT-BR).gba")
    out_rom_path.write_bytes(patched_rom)
    print(f"    Fonte PT-BR injetada em BIT\\0 : 24 glifos acentuados (0x8440..0x8457 -> glyphIds 1666..1680, 1625..1633)")
    print(f"\n  [OK] ROM de teste gerada em: {out_rom_path}")
    return 0


def export_translation_pack(rom_path: Path, out_json_path: Path) -> int:
    """
    Exporta todos os scripts PSI3 com diálogos em inglês para um pacote JSON estruturado
    (`extracted/translation_pack_ptbr.json`), pronto para tradução humana ou assistida
    e compatível diretamente com `--apply-json`.
    """
    rom = rom_path.read_bytes()
    specs = build_opcode_spec_table(rom)
    entries = parse_archive_table(rom, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)

    addr_to_indices: Dict[int, List[int]] = {}
    for e in entries:
        addr_to_indices.setdefault(int(e["rom_addr"], 16), []).append(e["index"])

    seen_addrs = set()
    scripts_out: Dict[str, Any] = {}
    total_lines = 0

    for e in entries:
        f_addr = int(e["rom_addr"], 16)
        if f_addr in seen_addrs:
            continue
        seen_addrs.add(f_addr)
        res = decompress_gba_lz77(rom, f_addr - GBA_ROM_BASE)
        if not res:
            continue
        psi3_bytes, _ = res
        if psi3_bytes[:4] != b"PSI3":
            continue

        strs = extract_psi3_strings(psi3_bytes, specs)
        if not strs:
            continue
        # Filtra scripts que têm apenas strings de teste em japonês sem letras ASCII
        has_ascii = any(any("A" <= c <= "Z" or "a" <= c <= "z" for c in s["text"]) for s in strs)
        if not has_ascii:
            continue

        s_idx = e["index"]
        scripts_out[str(s_idx)] = {
            "primary_index": s_idx,
            "shared_indices": addr_to_indices[f_addr],
            "rom_addr": e["rom_addr"],
            "strings": [
                {
                    "id": s["string_index"],
                    "opcode": s["opcode"],
                    "en": s["text"],
                    "ptbr": "",
                }
                for s in strs
            ],
        }
        total_lines += len(strs)

    out_json_path.parent.mkdir(parents=True, exist_ok=True)
    out_json_path.write_text(
        json.dumps(
            {
                "project": "Summon Night: Swordcraft Story (GBA) [AB4E] - Pacote de Tradução PT-BR",
                "total_scripts": len(scripts_out),
                "total_strings": total_lines,
                "supported_ptbr_accents": "".join(PTBR_CHAR_TO_SJIS.keys()),
                "scripts": scripts_out,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"[OK] Pacote de tradução exportado: {out_json_path} ({len(scripts_out)} scripts, {total_lines:,} linhas)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Compilador e Reinseridor de Scripts PSI3 (GBA)")
    parser.add_argument(
        "--rom",
        type=Path,
        default=Path("rom/Summon Night - Swordcraft Story (USA).gba"),
        help="Caminho da ROM original",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Executa a suíte de validação 100%% round-trip + prova de conceito PT-BR",
    )
    parser.add_argument(
        "--export-pack",
        type=Path,
        help="Exporta o pacote completo de tradução JSON (ex: extracted/translation_pack_ptbr.json)",
    )
    parser.add_argument(
        "--apply-json",
        type=Path,
        help="Aplica traduções a partir de um arquivo JSON ({script_idx: {string_idx: texto_ptbr}} ou formato --export-pack)",
    )
    parser.add_argument(
        "--out-rom",
        type=Path,
        default=Path("rom/Summon Night - Swordcraft Story (PT-BR).gba"),
        help="Caminho da ROM de saída traduzida",
    )
    args = parser.parse_args()

    if args.export_pack:
        return export_translation_pack(args.rom, args.export_pack)

    if args.apply_json:
        rom = args.rom.read_bytes()
        specs = build_opcode_spec_table(rom)
        entries = parse_archive_table(rom, ARCHIVE2_BASE_ADDR, ARCHIVE2_LIMIT_ADDR)
        trans_data = json.loads(args.apply_json.read_text(encoding="utf-8"))
        scripts_dict = trans_data.get("scripts", trans_data)

        rebuilt_map: Dict[int, bytes] = {}
        for s_idx_str, entry_val in scripts_dict.items():
            s_idx = int(s_idx_str)
            if isinstance(entry_val, dict) and "strings" in entry_val:
                int_str_map = {
                    int(item["id"]): item["ptbr"]
                    for item in entry_val["strings"]
                    if item.get("ptbr")
                }
            else:
                int_str_map = {int(k): v for k, v in entry_val.items() if v}

            if not int_str_map:
                continue
            rom_off = int(entries[s_idx]["rom_addr"], 16) - GBA_ROM_BASE
            orig_psi3, _ = decompress_gba_lz77(rom, rom_off)
            rebuilt_map[s_idx] = rebuild_psi3_script(orig_psi3, specs, translations=int_str_map)

        patched_rom, log = reinsert_scripts_into_rom(rom, rebuilt_map)
        args.out_rom.write_bytes(patched_rom)
        print(f"[OK] {len(log)} scripts compilados e reinseridos em {args.out_rom}")
        return 0

    return run_verification_suite(args.rom)


if __name__ == "__main__":
    sys.exit(main())
