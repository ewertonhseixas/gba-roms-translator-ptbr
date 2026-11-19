#!/usr/bin/env python3
"""
System & Menu Text Extractor — Summon Night (NDS)
Extrai strings Shift-JIS limpas de arm9.bin e overlays_arm9 para 03-mensagens-do-sistema.md.
"""

import re
from pathlib import Path

SJIS_PATTERN = re.compile(
    rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\x20-\x7e\n\r]){4,}"
)
HAS_KANA_RE = re.compile(r"[\u3040-\u30ff]{2,}")


def scan_binary(bin_path: Path, label: str):
    data = bin_path.read_bytes()
    rows = []
    for m in SJIS_PATTERN.finditer(data):
        raw = m.group(0)
        try:
            text = raw.decode("shift_jis")
        except UnicodeDecodeError:
            continue
        if not HAS_KANA_RE.search(text):
            continue
        # Ignora strings com caracteres de controle estranhos
        if any(ord(c) < 0x20 and c not in ("\n", "\r") for c in text):
            continue
        clean = text.replace("\r\n", "<br>").replace("\n", "<br>").replace("|", "\\|")
        rows.append((f"{label} `0x{m.start():06X}` ({len(raw)}B)", clean))
    return rows


def main():
    base = Path("03_TRADUCAO_ROMS_NDS/jogos/Summon Night (Japan)")
    bin_dir = base / "extracted" / "bin"
    out_md = base / "ARQUIVOS md" / "03-mensagens-do-sistema.md"

    all_rows = []
    arm9_dec = bin_dir / "arm9_dec.bin"
    arm9 = arm9_dec if arm9_dec.exists() else (bin_dir / "arm9.bin")
    if arm9.exists():
        all_rows.extend(scan_binary(arm9, arm9.name))

    ov_dir = bin_dir / "overlays_arm9"
    if ov_dir.exists():
        for ov in sorted(ov_dir.glob("*.bin")):
            all_rows.extend(scan_binary(ov, ov.name))

    lines = [
        "# 🖥️ Mensagens do Sistema e Menus — Summon Night (NDS)",
        "",
        f"> **Total de strings extraídas:** {len(all_rows)}",
        "",
        "| Origem / Offset | Contexto | Texto Original (JA-JP) | Tradução Sugerida (PT-BR) | Status |",
        "| :--- | :--- | :--- | :--- | :---: |",
    ]
    for loc, txt in all_rows:
        lines.append(f"| {loc} | Sistema/Menu | {txt} | | Pendente |")

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Extraído: {len(all_rows)} strings de sistema/menus para {out_md}")


if __name__ == "__main__":
    main()
