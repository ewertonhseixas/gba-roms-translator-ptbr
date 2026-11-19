"""Gerador de lotes Markdown (5 Pilares) para Tales of Hearts (NDS)."""
import re
import sys
from pathlib import Path

BASE_DIR = Path(
    "03_TRADUCAO_ROMS_NDS/jogos/Tales of Hearts - Anime Movie Edition (Japan)"
)
DATA_DIR = BASE_DIR / "extracted/nitrofs/data"
OUT_MD = BASE_DIR / "ARQUIVOS md"

ASCII_RUN_RE = re.compile(rb"[\x20-\x7e]{3,}")


def extract_strings(files: list[Path], min_len: int = 4) -> list[tuple[str, int, str]]:
    results: list[tuple[str, int, str]] = []
    for f in files:
        raw = f.read_bytes()
        for m in ASCII_RUN_RE.finditer(raw):
            text = m.group(0).decode("ascii").replace("|", "\\|").strip()
            if len(text) >= min_len and any(c.isalpha() for c in text):
                results.append((f.name, m.start(), text))
    return results


def write_md_table(out_path: Path, title: str, rows: list[tuple[str, int, str]]) -> None:
    lines = [
        f"# {title}",
        "",
        "| Arquivo | Offset | Original (EN) | Tradução (PT-BR) |",
        "| :--- | :--- | :--- | :--- |",
    ]
    for fname, off, text in rows:
        lines.append(f"| `{fname}` | `0x{off:X}` | {text} | |")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT_MD.mkdir(parents=True, exist_ok=True)

    # 1. Itens e Equipamentos (06-)
    item_files = sorted(f for f in (DATA_DIR / "item").rglob("*") if f.is_file())
    item_rows = extract_strings(item_files, min_len=3)
    write_md_table(
        OUT_MD / "06-itens-equipamentos-e-descricoes.md",
        "🎒 Itens, Equipamentos e Lojas — Tales of Hearts (EN -> PT-BR)",
        item_rows,
    )
    print(f"06-itens-equipamentos-e-descricoes.md: {len(item_rows)} linhas")

    # 2. Mensagens do Sistema / Menus (03-)
    menu_files = sorted(f for f in (DATA_DIR / "menu").rglob("*") if f.is_file())
    menu_rows = extract_strings(menu_files, min_len=3)
    write_md_table(
        OUT_MD / "03-mensagens-do-sistema.md",
        "⚙️ Mensagens do Sistema e Menus — Tales of Hearts (EN -> PT-BR)",
        menu_rows,
    )
    print(f"03-mensagens-do-sistema.md: {len(menu_rows)} linhas")

    # 3. Lotes de Diálogos (data/s/) - primeiros 5 lotes de 500 linhas
    s_files = sorted(f for f in (DATA_DIR / "s").iterdir() if f.is_file())
    s_rows = extract_strings(s_files[:150], min_len=4)
    batch_size = 500
    for idx in range(5):
        chunk = s_rows[idx * batch_size : (idx + 1) * batch_size]
        if not chunk:
            break
        batch_path = OUT_MD / f"lote-{idx + 1:02d}-dialogos.md"
        write_md_table(
            batch_path,
            f"💬 Lote {idx + 1:02d} de Diálogos (`data/s/`) — Tales of Hearts (EN -> PT-BR)",
            chunk,
        )
        print(f"{batch_path.name}: {len(chunk)} linhas")

    return 0


if __name__ == "__main__":
    sys.exit(main())
