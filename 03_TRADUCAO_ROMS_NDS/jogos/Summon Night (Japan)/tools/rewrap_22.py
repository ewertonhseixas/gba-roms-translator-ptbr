#!/usr/bin/env python3
"""Re-quebra todas as traduções PT-BR dos arquivos de diálogo para <= 22 caracteres/linha."""

import re
from pathlib import Path


def wrap_22(text: str) -> str:
    text = text.replace("<br>", " ")
    text = re.sub(r"\s+", " ", text).strip()
    lines = []
    while len(text) > 22:
        cut = text.rfind(" ", 0, 23)
        if cut <= 0:
            cut = 22
        lines.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        lines.append(text)
    return "<br>".join(lines)


def main():
    md_dir = Path("03_TRADUCAO_ROMS_NDS/jogos/Summon Night (Japan)/ARQUIVOS md")
    row_re = re.compile(
        r"^(\|\s*`0x[0-9A-Fa-f]+`\s*\(\d+B\)\s*\|\s*[^|]*\|\s*[^|]*\|\s*)([^|]*)(\|\s*[^|]*\|)$"
    )
    fixed_files = 0
    for md in sorted(md_dir.glob("*-dialogos-scn*.md")):
        out = []
        changed = False
        for line in md.read_text(encoding="utf-8").splitlines():
            m = row_re.match(line)
            if m and m.group(2).strip():
                new_pt = wrap_22(m.group(2).strip())
                if new_pt != m.group(2).strip():
                    changed = True
                out.append(f"{m.group(1)}{new_pt} {m.group(3)}")
            else:
                out.append(line)
        if changed:
            md.write_text("\n".join(out) + "\n", encoding="utf-8")
            fixed_files += 1
    print(f"Arquivos re-quebrados para <=22 chars: {fixed_files}")


if __name__ == "__main__":
    main()
