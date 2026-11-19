"""Compile the canonical PT-BR ROM from the validated graphics and dialogue batches."""

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from build_expanded_dialogues import BASE, build
from patch_followup_art import apply


def main():
    build_dir = BASE / "build"
    source = build_dir / "Summon-Night-PT-BR-Abertura-Corrigida.nds"
    output = build_dir / "Summon Night (PT-BR).nds"
    backup = build_dir / "Summon Night (PT-BR antes da abertura).nds"
    # On Windows, a private temporary directory gives its files a restrictive
    # ACL. Stage beside the ROM so it inherits the build directory permissions.
    with NamedTemporaryFile(prefix="compilar-ptbr-", suffix=".nds",
                            dir=build_dir, delete=False) as temp:
        staged = Path(temp.name)
    try:
        build(source, staged, set(), graphics=apply)
        if output.exists() and not backup.exists():
            shutil.copyfile(output, backup)
        staged.replace(output)
    finally:
        staged.unlink(missing_ok=True)
    print(f"ROM PT-BR: {output}")


if __name__ == "__main__":
    main()
