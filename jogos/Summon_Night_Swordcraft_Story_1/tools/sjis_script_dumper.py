#!/usr/bin/env python3
"""
Summon Night: Swordcraft Story (USA) [AB4E]
Shift-JIS Full-Width & PSI3 Script Dialogue Decoder
===================================================
Baseado na engenharia reversa de:
  - Text_FetchNextChar   (0x08009C38)
  - Text_StrLen          (0x08009DB0)
  - Font_GetGlyphBitmap  (0x08007724) -> Tabela SJIS @ 0x081DB270, Fonte BIT\0 @ 0x087077EC
  - Opcode 0x0218        (0x0800AF18 - Dialogue String)
  - Opcode 0x0220/0x0221 (0x0800B318 / 0x0800B344 - Choice/Menu Strings)

Decodifica as strings de 16 bits (Shift-JIS Full-Width + códigos de controle 83Cx / 87xx)
em todos os 2.639 scripts PSI3 do Archive #2 (0x085C10DC) e nas tabelas fixas da ROM.
"""

import json
import struct
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from archive_extractor import parse_archive_table, decompress_gba_lz77

GBA_ROM_BASE = 0x08000000

# Mapeamento especial de pontuação Shift-JIS (0x81xx) para ASCII legível
SJIS_81_MAP: Dict[int, str] = {
    0x8140: " ",
    0x8141: ",",
    0x8142: ".",
    0x8143: ",",
    0x8144: ".",
    0x8145: "·",
    0x8146: ":",
    0x8147: ";",
    0x8148: "?",
    0x8149: "!",
    0x815B: "ー",
    0x815C: "—",
    0x815D: "-",
    0x815E: "/",
    0x8160: "~",
    0x8163: "...",
    0x8165: "'",
    0x8166: "'",
    0x8167: '"',
    0x8168: '"',
    0x8169: "(",
    0x816A: ")",
    0x816D: "[",
    0x816E: "]",
    0x8175: "「",
    0x8176: "」",
    0x817B: "+",
    0x817C: "-",
    0x8181: "=",
    0x8183: "<",
    0x8184: ">",
    0x8193: "%",
    0x8194: "#",
    0x8195: "&",
    0x8196: "*",
    0x8197: "@",
    0x819C: "♡",
    0x81F4: "♪",
    0x84A1: "",  # Metade direita do glifo duplo '♡' (0x819C + 0x84A1)
    0x84A2: "",  # Metade direita do glifo duplo '...' (0x8163 + 0x84A2)
    0x84A3: "",  # Metade direita do glifo duplo '♪' (0x81F4 + 0x84A3)
}

# Variáveis de texto dinâmicas identificadas em sub_0800A0F4 (0x0800A100) e sub_08009C38
VAR_NAMES: Dict[int, str] = {
    0x0: "{PLAYER}",
    0x1: "{PARTNER}",
    0x2: "{VAR_2}",
    0x3: "{SIBLING}",   # "Big Bro" / "Big Sis"
    0x4: "{VAR_4}",
    0x5: "{MASTER}",    # "Hayato" / "Touya" / "Natsumi" / "Aya"
}


def decode_sjis_u16(halfword_le: int) -> Optional[str]:
    """
    Converte uma halfword little-endian lida por `ldrh` em `sub_08009C38` / `sub_08007724`
    para seu caractere correspondente ou tag de controle.
    Retorna None se não for um código válido da engine de texto.
    """
    b0 = halfword_le & 0xFF         # Primeiro byte na ROM (ex: 0x82, 0x81, 0x83, 0x87)
    b1 = (halfword_le >> 8) & 0xFF  # Segundo byte na ROM
    sjis_be = (b0 << 8) | b1

    # 1. Variáveis dinâmicas: b0 == 0x83 e (b1 & 0xF0) == 0xC0 -> 83 C0 .. 83 CF
    if b0 == 0x83 and (b1 & 0xF0) == 0xC0:
        var_idx = b1 & 0x0F
        return VAR_NAMES.get(var_idx, f"{{VAR_{var_idx:X}}}")

    # 2. Comandos de controle de janela/efeito: 87 40 .. 87 4F
    if b0 == 0x87 and (b1 & 0xF0) == 0x40:
        return f"{{CMD_874{b1 & 0xF:X}}}"

    # 3. Comandos de cor de fonte: 87 70 .. 87 7F
    if b0 == 0x87 and (b1 & 0xF0) == 0x70:
        return f"{{COLOR_{b1 & 0xF:X}}}"

    # 4. Outros controles 0x87xx (ex: quebra de linha / ícones)
    if b0 == 0x87 and 0x40 <= b1 <= 0x9F:
        return f"{{TAG_87{b1:02X}}}"

    # 5. Algarismos Full-Width (0x824F..0x8258 -> '0'..'9')
    if 0x824F <= sjis_be <= 0x8258:
        return chr(ord("0") + (sjis_be - 0x824F))

    # 6. Letras Maiúsculas Full-Width (0x8260..0x8279 -> 'A'..'Z')
    if 0x8260 <= sjis_be <= 0x8279:
        return chr(ord("A") + (sjis_be - 0x8260))

    # 7. Letras Minúsculas Full-Width (0x8281..0x829A -> 'a'..'z')
    if 0x8281 <= sjis_be <= 0x829A:
        return chr(ord("a") + (sjis_be - 0x8281))

    # 8. Pontuação Full-Width comum (0x81xx)
    if sjis_be in SJIS_81_MAP:
        return SJIS_81_MAP[sjis_be]

    # 9. Outros caracteres Shift-JIS válidos (Hiragana, Katakana, Kanji para textos de debug)
    if (0x8140 <= sjis_be <= 0x9FFC) or (0xE040 <= sjis_be <= 0xEAA4):
        try:
            return bytes([b0, b1]).decode("shift_jis")
        except UnicodeDecodeError:
            return None

    return None


def scan_psi3_for_english_strings(decomp: bytes, min_chars: int = 5) -> List[Dict[str, Any]]:
    """
    Varre um arquivo de script PSI3 descomprimido em busca de sequências de
    halfwords (16-bit) terminadas em 0x0000 que formam frases em inglês (Full-Width SJIS).
    """
    found = []
    # Alinhamento em 2 bytes (todos os opcodes e strings em PSI3 são alinhados em 16 bits!)
    n = len(decomp) & ~1
    i = 0x10  # Pula o cabeçalho de 16 bytes "PSI3"
    while i < n - 2:
        hw = struct.unpack_from("<H", decomp, i)[0]
        ch = decode_sjis_u16(hw)
        if ch is not None:
            start_off = i
            tokens = []
            ascii_letters = 0
            while i < n:
                hw = struct.unpack_from("<H", decomp, i)[0]
                if hw == 0x0000:
                    i += 2
                    break
                c = decode_sjis_u16(hw)
                if c is None:
                    break
                tokens.append(c)
                if len(c) == 1 and c.isalpha() and c.isascii():
                    ascii_letters += 1
                i += 2
            # Verifica se terminou em 0x0000 e possui letras suficientes
            if len(tokens) >= min_chars and ascii_letters >= 3:
                # Confere se o halfword anterior era um opcode de texto conhecido (ex: 0x0218, 0x0220, 0x0221)
                prev_hw = struct.unpack_from("<H", decomp, start_off - 2)[0] if start_off >= 0x12 else 0
                text = "".join(tokens)
                found.append({
                    "offset": f"0x{start_off:04X}",
                    "prev_u16": f"0x{prev_hw:04X}",
                    "char_count": len(tokens),
                    "text": text,
                })
        else:
            i += 2
    return found


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    rom = Path("rom/Summon Night - Swordcraft Story (USA).gba").read_bytes()
    arc2_entries = parse_archive_table(rom, 0x085C10DC, 0x0870771C)

    scripts_with_eng_dialogue = []
    total_strings = 0
    seen_rom_addrs = set()

    for ent in arc2_entries:
        if ent["rom_addr"] in seen_rom_addrs:
            continue
        seen_rom_addrs.add(ent["rom_addr"])

        res = decompress_gba_lz77(rom, ent["file_offset"])
        if not res:
            continue
        decomp, _ = res
        strs = scan_psi3_for_english_strings(decomp, min_chars=4)
        if strs:
            total_strings += len(strs)
            scripts_with_eng_dialogue.append({
                "file_index": ent["index"],
                "rom_addr": ent["rom_addr"],
                "decomp_size": len(decomp),
                "string_count": len(strs),
                "strings": strs,
            })

    # Também varre a região de dados estáticos da ROM (0x08070000..0x081FC000) para nomes de itens, armas, magias e menus!
    static_chunk = rom[0x070000:0x1FC000]
    static_strings = []
    i = 0
    n = len(static_chunk) & ~1
    while i < n - 2:
        hw = struct.unpack_from("<H", static_chunk, i)[0]
        c = decode_sjis_u16(hw)
        if c is not None and ((len(c) == 1 and c.isalnum() and c.isascii()) or c.startswith("{")):
            start = i
            tokens = []
            ascii_cnt = 0
            while i < n:
                hw = struct.unpack_from("<H", static_chunk, i)[0]
                if hw == 0x0000:
                    i += 2
                    break
                c = decode_sjis_u16(hw)
                if c is None:
                    break
                tokens.append(c)
                if len(c) == 1 and c.isalpha() and c.isascii():
                    ascii_cnt += 1
                i += 2
            if len(tokens) >= 3 and ascii_cnt >= 3:
                static_strings.append({
                    "rom_addr": f"0x{0x08070000 + start:08X}",
                    "text": "".join(tokens),
                })
        else:
            i += 2

    out_report = {
        "total_unique_psi3_files_with_english": len(scripts_with_eng_dialogue),
        "total_dialogue_strings_extracted": total_strings,
        "total_static_rom_strings_extracted": len(static_strings),
        "static_rom_strings_sample": static_strings[:80],
        "psi3_scripts_sample": scripts_with_eng_dialogue[:25],
    }

    out_path = Path("extracted/english_dialogue_dump.json")
    out_path.write_text(json.dumps(out_report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=" * 92)
    print(" EXTRAÇÃO DE DIÁLOGOS EM INGLÊS (SHIFT-JIS 16-BIT FULL-WIDTH) CONCLUÍDA!")
    print("=" * 92)
    print(f" • Scripts PSI3 únicos com diálogos em inglês : {len(scripts_with_eng_dialogue)}")
    print(f" • Total de falas/diálogos extraídos (PSI3)  : {total_strings}")
    print(f" • Strings fixas na ROM (Itens/Menus/Nomes)  : {len(static_strings)}")
    print("-" * 92)
    print(" [AMOSTRA DE STRINGS FIXAS NA ROM (0x08070000..0x081FC000)]")
    for s in static_strings[:15]:
        print(f"   {s['rom_addr']}: {s['text']}")
    print("-" * 92)
    print(" [AMOSTRA DE DIÁLOGOS EXTRAÍDOS DOS SCRIPTS PSI3 (ARCHIVE #2)]")
    for sc in scripts_with_eng_dialogue[:6]:
        print(f"\n  [Script #{sc['file_index']:04d} @ {sc['rom_addr']} ({sc['string_count']} falas)]")
        for st in sc["strings"][:5]:
            print(f"    +{st['offset']} (Opcode ant: {st['prev_u16']}): {st['text']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
