"""List translated entries that cannot yet be safely inserted."""

import csv
import re
from collections import Counter
from pathlib import Path

from rtz_dialogue_tool import patch_dialogue_slots
from translation_markdown import plain_translation, split_md_row

BASE = Path(__file__).resolve().parents[1]
REFERENCE = re.compile(r"0x([0-9A-Fa-f]+).*?\((\d+)B\)")


def audit():
    pending_by_scene = {}
    counts = Counter()
    report = BASE / "auditoria-de-insercao-ptbr.csv"
    with report.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["Lote", "Linha", "Referência", "Pendência", "Tradução"])
        for path in sorted((BASE / "ARQUIVOS md").glob("*.md")):
            system = path.name.startswith("03-")
            scene_match = re.search(r"dialogos-(scn\w+)", path.stem)
            if not system and not scene_match:
                continue
            pending = {}
            if scene_match:
                scene = scene_match[1]
                if scene not in pending_by_scene:
                    first = path.with_name(re.sub(r"-lote-\d+$", "", path.stem) + ".md")
                    source = BASE / "extracted" / "rtz_unpacked" / "scnrts" / (scene + ".rtz")
                    _, _, deferred = patch_dialogue_slots(first, source.read_bytes())
                    pending_by_scene[scene] = dict(deferred)
                pending = pending_by_scene[scene]
            for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if not line.startswith("|"):
                    continue
                cells = split_md_row(line)
                ref = REFERENCE.search(cells[0])
                if not ref:
                    continue
                counts["entradas"] += 1
                offset, capacity = int(ref[1], 16), int(ref[2])
                reason = pending.get(offset, "")
                translation = cells[3] if len(cells) == 5 else ""
                if not translation:
                    reason = "tradução ausente ou linha malformada"
                elif system:
                    try:
                        length = len(plain_translation(translation).replace("<br>", "\n").encode("cp1252"))
                        if length > capacity:
                            reason = f"{length}/{capacity} bytes"
                    except UnicodeEncodeError:
                        reason = "caractere fora de CP1252"
                if reason:
                    writer.writerow([path.name, number, cells[0], reason, translation])
                    counts["sistema" if system else "diálogo"] += 1
                    if reason.startswith("operando"):
                        counts["operandos"] += 1
    print(dict(counts))


if __name__ == "__main__":
    audit()
