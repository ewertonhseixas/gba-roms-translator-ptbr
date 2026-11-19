#!/usr/bin/env python3
"""
NDS Feature Detector & NitroFS Auditor
Inspeciona uma ROM de Nintendo DS (.nds) usando ndspy e gera um relatório técnico
em Markdown com cabeçalho, overlays, contagem de extensões no NitroFS e próximos passos.
"""

import argparse
import os
from collections import Counter
from pathlib import Path
import ndspy.rom


def walk_nitrofs(root_filenames, folder=None, prefix=""):
    """Percorre recursivamente os arquivos do NitroFS retornando (caminho, file_id)."""
    if folder is None:
        folder = root_filenames
    results = []
    for name in folder.files:
        full_path = f"{prefix}/{name}" if prefix else name
        fid = root_filenames.idOf(full_path)
        results.append((full_path, fid))
    for sub_name, sub_folder in folder.folders:
        sub_prefix = f"{prefix}/{sub_name}" if prefix else sub_name
        results.extend(walk_nitrofs(root_filenames, sub_folder, sub_prefix))
    return results


def analyze_nds(rom_path: Path, output_path: Path | None = None):
    rom = ndspy.rom.NintendoDSRom.fromFile(str(rom_path))

    title = rom.name.decode("ascii", errors="replace").strip("\x00 ")
    game_code = rom.idCode.decode("ascii", errors="replace")
    arm9_size = len(rom.arm9)
    arm7_size = len(rom.arm7)
    arm9_ovts = len(rom.loadArm9Overlays())
    arm7_ovts = len(rom.loadArm7Overlays())

    files = walk_nitrofs(rom.filenames)
    ext_counter = Counter()
    total_nitro_bytes = 0

    for fpath, fid in files:
        ext = Path(fpath).suffix.lower() or "(sem extensão)"
        ext_counter[ext] += 1
        if fid < len(rom.files):
            total_nitro_bytes += len(rom.files[fid])

    lines = [
        f"# Relatório Técnico de Extração NDS: {rom_path.name}",
        "",
        "## 1. Cabeçalho e Binários Principais",
        f"- **Arquivo:** `{rom_path.name}` ({rom_path.stat().st_size / (1024*1024):.2f} MB)",
        f"- **Título Interno:** `{title}`",
        f"- **Game Code:** `{game_code}`",
        f"- **ARM9:** {arm9_size:,} bytes | **Overlays ARM9:** {arm9_ovts}",
        f"- **ARM7:** {arm7_size:,} bytes | **Overlays ARM7:** {arm7_ovts}",
        "",
        "## 2. Inventário do NitroFS",
        f"- **Total de Arquivos:** {len(files):,}",
        f"- **Tamanho Total Descompactado (NitroFS):** {total_nitro_bytes / (1024*1024):.2f} MB",
        "",
        "| Extensão | Quantidade | Observação |",
        "| :--- | :---: | :--- |",
    ]

    notes = {
        ".narc": "Arquivo contêiner (Nitro Archive)",
        ".nftr": "Fonte bitmap/vetorial NDS (Nitro Font)",
        ".ncgr": "Tiles gráficos (Nitro Character Graphic)",
        ".nclr": "Paleta de cores (Nitro Color)",
        ".nscr": "Tilemap/Tela (Nitro Screen)",
        ".ncer": "Células/Sprites (Nitro Cell)",
        ".nanr": "Animações (Nitro Animation)",
        ".sdat": "Áudio/Música (Sound Data)",
        ".bin": "Dados binários / scripts / tabelas",
        ".dat": "Dados gerais / scripts",
    }

    for ext, count in ext_counter.most_common():
        obs = notes.get(ext, "-")
        lines.append(f"| `{ext}` | {count:,} | {obs} |")

    lines.extend([
        "",
        "## 3. Próximos Passos Recomendados",
        "1. Extrair o NitroFS completo para `extracted/nitrofs/` para inspeção de textos e fontes.",
        "2. Localizar arquivos de texto (em `.narc`, `.bin`, `.dat` ou `arm9.bin` / overlays).",
        "3. Verificar se há fontes `.nftr` ou fontes customizadas para suporte a acentuação PT-BR.",
        "4. Popular `ARQUIVOS md/` com os 5 Pilares Markdown e rodar `metrics_analyzer.py` + `qa_gate_hook.py`.",
    ])

    report = "\n".join(lines) + "\n"

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
        print(f"Relatório salvo em: {output_path}")
    else:
        print(report)


def main():
    parser = argparse.ArgumentParser(description="Auditoria técnica de ROMs Nintendo DS (.nds)")
    parser.add_argument("rom", type=Path, help="Caminho para o arquivo .nds")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Caminho do relatório .md de saída")
    args = parser.parse_args()

    if not args.rom.exists():
        raise FileNotFoundError(f"ROM não encontrada: {args.rom}")

    analyze_nds(args.rom, args.output)


if __name__ == "__main__":
    main()
