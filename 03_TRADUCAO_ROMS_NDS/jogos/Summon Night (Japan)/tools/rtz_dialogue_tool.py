#!/usr/bin/env python3
"""
RTZ Dialogue Extractor & Injector — Summon Night (NDS)
Extrai strings Shift-JIS de arquivos .rtz descomprimidos para o padrão dos 5 Pilares Markdown
e permite reinjetar traduções PT-BR (com padding/validação de tamanho e recomprimido em LZ10).
"""

import argparse
import re
import struct
from functools import cache
from pathlib import Path

from translation_markdown import batch_lines, plain_translation, split_md_row

PTBR_SJIS_MAP: dict[str, bytes] = {
    "À": b"\x88\xA2", "Á": b"\x88\xA3", "Â": b"\x88\xA4", "Ã": b"\x88\xA5",
    "Ç": b"\x88\xAB", "É": b"\x88\xAC", "Ê": b"\x88\xB3", "Í": b"\x88\xB5",
    "Ó": b"\x88\xB6", "Ô": b"\x88\xBB", "Õ": b"\x88\xC0", "Ú": b"\x88\xC3",
    "à": b"\x88\xC4", "á": b"\x88\xC5", "â": b"\x88\xC8", "ã": b"\x88\xC9",
    "ç": b"\x88\xCA", "é": b"\x88\xCB", "ê": b"\x88\xCC", "í": b"\x88\xCD",
    "ó": b"\x88\xCF", "ô": b"\x88\xD0", "õ": b"\x88\xD3", "ú": b"\x88\xD4",
}


def encode_ptbr_sjis(text: str) -> bytes:
    out = bytearray()
    for ch in text:
        if ch in PTBR_SJIS_MAP:
            out.extend(PTBR_SJIS_MAP[ch])
        else:
            out.extend(ch.encode("shift_jis"))
    return bytes(out)

# Sequências válidas de texto Shift-JIS japonês (com pontuação/quebras comuns)
SJIS_PATTERN = re.compile(
    rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e\n\r]){4,}"
)
HAS_JP_RE = re.compile(r"[\u3040-\u30ff]{2,}")


def extract_rtz_to_md(rtz_path: Path, md_out: Path):
    data = rtz_path.read_bytes()
    rows = []

    for m in SJIS_PATTERN.finditer(data):
        raw = m.group(0)
        try:
            text = raw.decode("shift_jis")
        except UnicodeDecodeError:
            continue
        if not HAS_JP_RE.search(text):
            continue

        offset = m.start()
        byte_len = len(raw)
        clean_text = text.replace("\r\n", "<br>").replace("\n", "<br>").replace("|", "\\|")
        rows.append((offset, byte_len, clean_text))

    lines = [
        f"# Diálogos Extraídos: `{rtz_path.name}`",
        "",
        f"> **Arquivo:** `{rtz_path.name}` | **Falas extraídas:** {len(rows)}",
        "",
        "| Script / Offset | Personagem / Contexto | Texto Original (JA-JP) | Tradução Sugerida (PT-BR) | Status |",
        "| :--- | :--- | :--- | :--- | :---: |",
    ]
    for offset, byte_len, txt in rows:
        lines.append(f"| `0x{offset:06X}` ({byte_len}B) | - | {txt} | | Pendente |")

    md_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Extraído: {rtz_path.name} -> {md_out.name} ({len(rows)} falas)")


def wrap_text(text: str, max_chars: int = 26) -> str:
    """Quebra linhas que ultrapassem max_chars no último espaço disponível."""
    out_lines = []
    for line in text.split("\n"):
        while len(line) > max_chars:
            cut = line.rfind(" ", 0, max_chars + 1)
            if cut <= 0:
                cut = max_chars
            out_lines.append(line[:cut].rstrip())
            line = line[cut:].lstrip()
        out_lines.append(line)
    return "\n".join(out_lines)


TEXT_OPERAND = re.compile(rb"\x33[\x01-\x04]\x7c\xf0\xc1(.)", re.S)
TEXT_CONTROL = re.compile(rb"@[A-Za-z][0-9]+|[\x00-\x09\x0B-\x1F]")
OPEN_CHOICE_WINDOW = bytes.fromhex("68007cf0c11522dd8c")


@cache
def dialogue_font_advances():
    font = (Path(__file__).resolve().parents[1] / "build/font12jp_ptbr.NFTR").read_bytes()
    offset = 16
    widths = []
    glyphs = {}
    while offset < len(font):
        tag, size = struct.unpack_from("<4sI", font, offset)
        if size < 8:
            raise ValueError("Bloco NFTR inválido")
        if tag == b"HDWC":
            first, last = struct.unpack_from("<HH", font, offset+8)
            widths = [12] * first + [font[offset+18+3*i] for i in range(last-first+1)]
        if tag == b"PAMC":
            first, last, kind = struct.unpack_from("<HHI", font, offset+8)
            if kind == 0:
                base = struct.unpack_from("<H", font, offset+20)[0]
                glyphs.update((n, base+n-first) for n in range(first, last+1))
            elif kind == 1:
                glyphs.update(zip(range(first, last+1), struct.unpack_from(
                    f"<{last-first+1}H", font, offset+20)))
            elif kind == 2:
                count = struct.unpack_from("<H", font, offset+20)[0]
                for i in range(count):
                    code, index = struct.unpack_from("<HH", font, offset+22+4*i)
                    glyphs[code] = index
        offset += size
    return {code: widths[index] for code, index in glyphs.items() if index < len(widths)}


def fit_dialogue_pixels(lines, line_budget):
    """Fit a continuous paragraph, keeping control codes and words together."""
    if not all(lines) or any(line.startswith(" ") for line in lines):
        return None
    try:
        advances = dialogue_font_advances()
        words = " ".join(lines).split()
        widths = [
            sum(advances.get(int.from_bytes(encode_ptbr_sjis(ch), "big"), 12) for ch in word)
            for word in words
        ]
    except UnicodeEncodeError:
        return None
    space = advances[32]
    limit = 130
    output = []
    current = []
    width = 0
    for word, advance in zip(words, widths, strict=True):
        if advance > limit:
            return None
        if current and width + space + advance > limit:
            output.append(" ".join(current))
            current = []
            width = 0
        width += advance + (space if current else 0)
        current.append(word)
    if current:
        output.append(" ".join(current))
    return output if len(output) <= line_budget else None


def script_without_text_operands(data: bytes):
    """Return the serialized instruction stream with text operands removed."""
    cursor = 0
    pieces = []
    for match in TEXT_OPERAND.finditer(data):
        if match.start() < cursor:
            continue
        end = match.end() + match[1][0]
        if data[end:end+1] != b"e":
            continue
        pieces.append(data[cursor:match.start()+5])
        cursor = end
    pieces.append(data[cursor:])
    return b"".join(pieces), len(pieces) - 1


def patch_dialogue_slots(md_path: Path, original: bytes, *, expand=False):
    """Patch verified text operands, keeping every opcode and branch operand."""
    reference = re.compile(r"0x([0-9A-Fa-f]+).*?\((\d+)B\)")
    markers = {bytes((0x33, kind, 0x7C, 0xF0, 0xC1)) for kind in range(1, 5)}
    edits = {}
    deferred = []
    for line in batch_lines(md_path):
        if not line.startswith("|"):
            continue
        cells = split_md_row(line)
        match = reference.search(cells[0])
        if len(cells) != 5 or not match or not (translation := plain_translation(cells[3])):
            continue
        offset, size = int(match[1], 16), int(match[2])
        end = offset + size - 1
        candidates = [
            pos for pos in (offset - 1, offset)
            if 5 <= pos < end < len(original) and original[pos-5:pos] in markers
            and original[pos] == end - pos - 1 and original[end] == 0x65
        ]
        if len(candidates) != 1:
            deferred.append((offset, "operando não reconhecido"))
            continue
        start = candidates[0] + 1
        lines = translation.split("<br>")
        source_text = original[start:end]
        choice = original[start-20:start-11] == OPEN_CHOICE_WINDOW
        source_lines = source_text.count(b"\n") + 1
        line_budget = max(4, source_lines) if expand else 4
        fitted_pixels = False
        if choice:
            # The cursor has its own column. Keep each option on its original row.
            lines = [
                ("\u3000" if source.startswith(b"\x81\x40") else "") + line.strip()
                for line, source in zip(lines, source_text.split(b"\n"))
            ] if len(lines) == source_lines else lines
        # Indented lines are menu entries and must keep their line positions.
        if not choice and not any(text.startswith(" ") for text in lines):
            lines = wrap_text("\n".join(lines), max_chars=22).split("\n")
            if expand and len(lines) > line_budget and all(lines):
                lines = wrap_text(" ".join(lines), max_chars=22).split("\n")
            if expand and len(lines) > line_budget:
                fitted = fit_dialogue_pixels(translation.split("<br>"), line_budget)
                if fitted:
                    lines = fitted
                    fitted_pixels = True
        try:
            encoded = encode_ptbr_sjis("\n".join(lines))
        except UnicodeEncodeError:
            deferred.append((offset, "caractere sem glifo"))
            continue
        issues = []
        if expand and len(encoded) >= 0xFC:
            issues.append("limite do operando de comprimento de um byte")
        if not expand and len(encoded) > end - start:
            issues.append(f"{len(encoded)}/{end-start} bytes")
        if expand and TEXT_CONTROL.findall(source_text) != TEXT_CONTROL.findall(encoded):
            issues.append("marcadores de controle divergentes")
        if expand and choice and len(lines) != source_lines:
            issues.append("quantidade de opções divergente")
        if len(lines) > line_budget or (not fitted_pixels and any(len(text.lstrip("\u3000")) > 22 for text in lines)):
            issues.append("limite da caixa de diálogo")
        if issues:
            deferred.append((offset, ", ".join(issues)))
            continue
        pos = start - 1
        if pos in edits:
            raise ValueError(f"Operando repetido em {md_path}: 0x{pos:06X}")
        body = encoded if expand else encoded.ljust(end-start, b"\0")
        edits[pos] = end, bytes((len(body),)) + body

    cursor = 0
    chunks = []
    for pos, (end, operand) in sorted(edits.items()):
        if pos < cursor:
            raise ValueError(f"Operandos sobrepostos em {md_path}: 0x{pos:06X}")
        chunks.extend((original[cursor:pos], operand))
        cursor = end
    chunks.append(original[cursor:])
    result = b"".join(chunks)
    if expand and script_without_text_operands(result) != script_without_text_operands(original):
        raise ValueError(f"A sequência de instruções mudou em {md_path}")
    return result, len(edits), deferred


def inject_md_to_rtz(md_path: Path, rtz_orig: Path, rtz_out: Path, compress_lz10: bool = True, *, expand=False):
    out_bytes, injected, deferred = patch_dialogue_slots(md_path, rtz_orig.read_bytes(), expand=expand)
    if compress_lz10:
        from patch_frontend import literal_lz10

        out_bytes = literal_lz10(out_bytes)
    rtz_out.parent.mkdir(parents=True, exist_ok=True)
    rtz_out.write_bytes(out_bytes)
    print(f"Injetado: {rtz_out.name} ({injected} falas, {len(deferred)} mantidas no original)")
    for offset, reason in deferred:
        print(f"0x{offset:06X}: {reason}")


def main():
    parser = argparse.ArgumentParser(description="Extrator/Injetor RTZ <-> Markdown (Summon Night NDS)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ext = sub.add_parser("extract", help="Extrai .rtz para .md")
    p_ext.add_argument("rtz", type=Path, help="Arquivo .rtz descomprimido")
    p_ext.add_argument("-o", "--output", type=Path, required=True, help="Arquivo .md de saída")

    p_inj = sub.add_parser("inject", help="Injeta .md traduzido no .rtz")
    p_inj.add_argument("md", type=Path, help="Arquivo .md traduzido")
    p_inj.add_argument("rtz_orig", type=Path, help="Arquivo .rtz descomprimido original")
    p_inj.add_argument("-o", "--output", type=Path, required=True, help="Arquivo .rtz de saída")
    p_inj.add_argument("--no-lz10", action="store_true", help="Não comprimir saída em LZ10")
    p_inj.add_argument("--expand", action="store_true", help="Permitir operandos de texto de tamanho variável")

    args = parser.parse_args()
    if args.cmd == "extract":
        extract_rtz_to_md(args.rtz, args.output)
    elif args.cmd == "inject":
        inject_md_to_rtz(args.md, args.rtz_orig, args.output, not args.no_lz10, expand=args.expand)


if __name__ == "__main__":
    main()
