#!/usr/bin/env python3
"""
Metrics Analyzer — Protocolo de Extração para Tradução de ROMs
=============================================================
Analisa arquivos Markdown de tradução compatíveis com o validador
e extrai estatísticas completas de métricas de caracteres:
  - Total de caixas de diálogo e falas
  - Contagem de linhas por caixa (via tags <br>)
  - Média, Mínimo, Máximo e Percentil 95 de caracteres por linha
  - Comparativo exato entre Texto Original (EN/JP) e Tradução (PT-BR)
  - Identificação de linhas com risco de overflow (> limite estipulado)
  - Gera automaticamente o relatório 'estudo-de-metricas-e-caracteres.md'
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def split_md_row(line: str) -> List[str]:
    """Divide uma linha de tabela Markdown formatada em células."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def clean_cell_text(raw: str) -> str:
    """Remove marcações Markdown (` ou **) e mantém quebras <br>."""
    s = raw.strip()
    s = s.replace("**", "").replace("`", "")
    return s


def parse_dialogue_lines(cell: str) -> List[str]:
    """Divide a célula em linhas individuais separadas por <br>."""
    cleaned = clean_cell_text(cell)
    lines = re.split(r"<br\s*/?>", cleaned, flags=re.IGNORECASE)
    # Filtra linhas vazias irrelevantes
    return [ln.strip() for ln in lines if ln.strip()]


def analyze_markdown_file(filepath: Path) -> List[Dict[str, Any]]:
    """Analisa um arquivo .md e extrai todas as entradas de diálogo com métricas."""
    entries = []
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_table = False
    en_col = None
    pt_col = None
    char_col = None

    for line_idx, line in enumerate(lines):
        line_str = line.strip()
        if line_str.startswith("|") and ("---" in line_str or ":---" in line_str):
            in_table = True
            continue

        if line_str.startswith("|") and not in_table:
            # Cabeçalho da tabela
            headers = [h.lower() for h in split_md_row(line_str)]
            for idx, h in enumerate(headers):
                if any(k in h for k in ("original", "en-us", "padrão")):
                    if en_col is None:
                        en_col = idx
                elif any(k in h for k in ("sugerid", "pt-br", "tradução")):
                    if pt_col is None:
                        pt_col = idx
                elif any(k in h for k in ("personagem", "speaker", "falante")):
                    char_col = idx
            continue

        if in_table:
            if not line_str.startswith("|"):
                in_table = False
                en_col = None
                pt_col = None
                char_col = None
                continue

            cells = split_md_row(line_str)
            if en_col is not None and pt_col is not None and len(cells) > max(en_col, pt_col):
                raw_en = cells[en_col]
                raw_pt = cells[pt_col]
                speaker = cells[char_col] if char_col is not None and len(cells) > char_col else ""

                en_lines = parse_dialogue_lines(raw_en)
                pt_lines = parse_dialogue_lines(raw_pt)

                if en_lines:
                    entries.append({
                        "file": filepath.name,
                        "line_idx": line_idx + 1,
                        "speaker": speaker,
                        "en_lines": en_lines,
                        "pt_lines": pt_lines,
                        "en_chars": [len(l) for l in en_lines],
                        "pt_chars": [len(l) for l in pt_lines],
                    })

    return entries


def compute_statistics(entries: List[Dict[str, Any]], hard_limit: int = 36) -> Dict[str, Any]:
    """Calcula estatísticas agregadas a partir de uma lista de entradas."""
    total_boxes = len(entries)
    if total_boxes == 0:
        return {}

    all_en_lines = []
    all_pt_lines = []
    en_box_line_counts = []
    pt_box_line_counts = []
    overflow_lines = []

    for e in entries:
        en_box_line_counts.append(len(e["en_lines"]))
        pt_box_line_counts.append(len(e["pt_lines"]))

        for l in e["en_lines"]:
            all_en_lines.append(len(l))

        for idx, l in enumerate(e["pt_lines"]):
            l_len = len(l)
            all_pt_lines.append(l_len)
            if l_len > hard_limit:
                overflow_lines.append({
                    "file": e["file"],
                    "line_idx": e["line_idx"],
                    "speaker": e["speaker"],
                    "text": l,
                    "length": l_len,
                    "line_in_box": idx + 1
                })

    def calc_stats(arr: List[int]) -> Dict[str, Any]:
        if not arr:
            return {"count": 0, "min": 0, "max": 0, "avg": 0.0, "p95": 0}
        s_arr = sorted(arr)
        p95_idx = int(len(s_arr) * 0.95)
        return {
            "count": len(arr),
            "min": s_arr[0],
            "max": s_arr[-1],
            "avg": round(sum(s_arr) / len(s_arr), 1),
            "p95": s_arr[min(p95_idx, len(s_arr) - 1)],
        }

    return {
        "total_boxes": total_boxes,
        "en_lines_stats": calc_stats(all_en_lines),
        "pt_lines_stats": calc_stats(all_pt_lines),
        "en_box_lines": calc_stats(en_box_line_counts),
        "pt_box_lines": calc_stats(pt_box_line_counts),
        "overflow_count": len(overflow_lines),
        "overflow_lines": overflow_lines,
    }


def generate_metrics_markdown_report(stats: Dict[str, Any], output_path: Path, game_name: str = "Novo Jogo GBA", hard_limit: int = 36):
    """Gera o arquivo de estudo de métricas em formato Markdown pronto para uso."""
    en_l = stats.get("en_lines_stats", {})
    pt_l = stats.get("pt_lines_stats", {})
    en_b = stats.get("en_box_lines", {})
    pt_b = stats.get("pt_box_lines", {})

    content = f"""# 📐 Estudo de Métricas de Caracteres por Linha de Diálogo
**Jogo:** {game_name}  
**Plataforma:** Game Boy Advance (GBA)  
**Teto Operacional de Caracteres (Hard Limit):** {hard_limit} caracteres/linha  
**Gerado por:** `metrics_analyzer.py` (Protocolo de Extração)  

---

## 🎯 1. Resumo Executivo das Métricas

| Métrica | Original (EN/JP) | Tradução (PT-BR) | Diferença (%) |
| :--- | :---: | :---: | :---: |
| **Total de Caixas de Diálogo** | `{stats.get("total_boxes", 0):,}` | `{stats.get("total_boxes", 0):,}` | `0%` |
| **Total de Linhas Renderizadas** | `{en_l.get("count", 0):,}` | `{pt_l.get("count", 0):,}` | `+{round((pt_l.get("count", 1) / max(en_l.get("count", 1), 1) - 1) * 100, 1)}%` |
| **Média de Caracteres por Linha** | `{en_l.get("avg", 0.0)}` | `{pt_l.get("avg", 0.0)}` | `+{round((pt_l.get("avg", 1) / max(en_l.get("avg", 1), 1) - 1) * 100, 1)}%` |
| **Mínimo de Caracteres em Linha** | `{en_l.get("min", 0)}` | `{pt_l.get("min", 0)}` | - |
| **Máximo de Caracteres em Linha** | `{en_l.get("max", 0)}` | `{pt_l.get("max", 0)}` | - |
| **Percentil 95 (P95) de Caracteres** | `{en_l.get("p95", 0)}` | `{pt_l.get("p95", 0)}` | - |
| **Média de Linhas por Caixa** | `{en_b.get("avg", 0.0)}` | `{pt_b.get("avg", 0.0)}` | - |

---

## 🚦 2. Zonas de Segurança e Limites Recomendados

| Faixa de Caracteres (PT-BR) | Classificação Visual | Condição de Uso |
| :---: | :---: | :--- |
| **1 a 32 caracteres** | 🟢 **Ideal (Seguro)** | Leitura confortável; sem qualquer risco de encostar na moldura. |
| **33 a 35 caracteres** | 🟡 **Atenção (Soft Limit)** | Permitido se a frase contiver caracteres finos (`i`, `l`, `t`, pontuação). |
| **36+ caracteres** | 🔴 **Crítico (Hard Limit)** | **Overflow potencial**. Exige quebra manual de linha (`<br>`) ou síntese. |

---

## ⚠️ 3. Linhas Acima do Limite Detectadas ({stats.get("overflow_count", 0)} ocorrências)

"""

    overflows = stats.get("overflow_lines", [])
    if not overflows:
        content += "> ✅ **Excelente!** Nenhuma linha no texto traduzido ultrapassa o limite de segurança de " + str(hard_limit) + " caracteres.\n"
    else:
        content += "| Arquivo | Linha | Falante / Contexto | Texto PT-BR | Comprimento | Excesso |\n"
        content += "| :--- | :---: | :--- | :--- | :---: | :---: |\n"
        for o in overflows[:50]:  # Limita aos primeiros 50 no resumo
            excess = o["length"] - hard_limit
            txt_escaped = o["text"].replace("|", "/")
            content += f"| `{o['file']}` | {o['line_idx']} | {o['speaker']} | `{txt_escaped}` | **{o['length']}** | +{excess} |\n"

        if len(overflows) > 50:
            content += f"\n*(Exibindo as primeiras 50 de {len(overflows)} linhas em excesso)*\n"

    output_path.write_text(content, encoding="utf-8")
    print(f"✅ Relatório de métricas gerado com sucesso em: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analisador de métricas de caracteres para tradução de ROMs")
    parser.add_argument("--dir", "-d", default="ARQUIVOS md", help="Diretório onde estão os arquivos .md")
    parser.add_argument("--limit", "-l", type=int, default=36, help="Limite máximo de caracteres por linha (padrão: 36)")
    parser.add_argument("--out", "-o", default=None, help="Caminho do arquivo Markdown de saída")
    parser.add_argument("--game", "-g", default="GBA Game", help="Nome do jogo analisado")

    args = parser.parse_args()
    target_dir = Path(args.dir)

    if not target_dir.exists():
        print(f"❌ Diretório não encontrado: {target_dir}")
        sys.exit(1)

    all_entries = []
    md_files = list(target_dir.rglob("*.md"))
    print(f"🔍 Escaneando {len(md_files)} arquivos Markdown em '{target_dir}'...")

    for f in md_files:
        # Pula arquivos de índice e templates
        if f.name.startswith(("00-", "01-", "TEMPLATE")) or "catalogo" in f.name.lower():
            continue
        entries = analyze_markdown_file(f)
        all_entries.extend(entries)

    print(f"📊 Total de falas/caixas de diálogo analisadas: {len(all_entries)}")
    stats = compute_statistics(all_entries, hard_limit=args.limit)

    en_stats = stats.get("en_lines_stats", {})
    pt_stats = stats.get("pt_lines_stats", {})
    print(f"📈 Média Original: {en_stats.get('avg', 0)} chars/linha | Máx: {en_stats.get('max', 0)} chars")
    print(f"📈 Média PT-BR:   {pt_stats.get('avg', 0)} chars/linha | Máx: {pt_stats.get('max', 0)} chars")
    print(f"⚠️  Linhas com estouro (> {args.limit} chars): {stats.get('overflow_count', 0)}")

    out_file = Path(args.out) if args.out else target_dir / "estudo-de-metricas-e-caracteres.md"
    generate_metrics_markdown_report(stats, out_file, game_name=args.game, hard_limit=args.limit)


if __name__ == "__main__":
    main()
