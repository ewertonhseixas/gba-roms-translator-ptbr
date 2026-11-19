"""Shared Markdown conventions for the validator and NDS injectors."""

import re
from pathlib import Path


def split_md_row(line: str) -> list[str]:
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def batch_lines(first: Path):
    yield from first.read_text(encoding="utf-8-sig").splitlines()
    if not re.search(r"-lote-\d+$", first.stem):
        for part in sorted(first.parent.glob(f"{first.stem}-lote-[0-9][0-9].md")):
            yield from part.read_text(encoding="utf-8-sig").splitlines()


def plain_translation(cell: str) -> str:
    return cell.replace("`", "").replace("**", "").replace(r"\|", "|")
