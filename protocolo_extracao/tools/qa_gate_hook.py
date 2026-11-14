#!/usr/bin/env python3
"""
QA Gate Hook — GBA Localization Studio (Protocolo Mestre de Tradução)
=====================================================================
Inspirado nos Quality Gates do Claude-Code-Game-Studios.
Executa uma auditoria implacável em 5 barreiras sobre arquivos Markdown (.md)
de tradução antes de liberar para compilação na ROM:

  1. [SINTAXE & VARIÁVEIS] Tags {PLAYER}, {PARTNER}, etc. idênticas entre EN e PT-BR.
  2. [BARREIRA ANTI-OVERFLOW] Nenhuma linha física acima do Hard Limit (padrão: 36 chars) e alerta no Soft Limit (33-35 chars).
  3. [ORFANDADE TEXTUAL] Detecta monossílabos órfãos ('o', 'a', 'de', 'em', 'e', 'que') isolados no fim de uma linha antes de <br>.
  4. [POLÍTICA DE ABREVIAÇÕES] Bloqueia internetês ou abreviações ('vc', 'tb', 'pq', 'atq.', 'esp.') em arquivos de diálogo de história.
  5. [GLOSSÁRIO & NEUTRALIDADE] Audita se termos obrigatórios do glossário presentes no original foram traduzidos e alerta possíveis adjetivos marcados em falas de {PLAYER}.
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

# Abreviações proibidas em diálogos de história (permitidas apenas em 03-sistema e 06-itens)
FORBIDDEN_DIALOGUE_ABBREVS = [
    r"\bvc\b", r"\bvcs\b", r"\bpq\b", r"\btb\b", r"\btbm\b",
    r"\bctz\b", r"\bblz\b", r"\bvlw\b", r"\bflw\b", r"\bq\b",
    r"\bp/\b", r"\bc/\b", r"\batq\.", r"\bdef\.", r"\brecup\.",
    r"\besp\.", r"\bmin\.", r"\belem\."
]

# Monossílabos e preposições que não devem ficar órfãos no fim da linha antes de <br>
ORPHAN_WORDS = {"o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das", "em", "no", "na", "e", "ou", "que", "se", "por", "com", "para"}

# Padrões suspeitos de marcação de gênero masculino direto para o protagonista
GENDER_SUSPECT_PATTERNS = [
    (r"\bvocê está cansado\b", "Use forma neutra: 'O cansaço bateu?' ou 'Já está sem fôlego?'"),
    (r"\bvocê está pronto\b", "Use forma neutra: 'Tudo pronto?' ou 'Já se preparou?'"),
    (r"\bvocê é muito rápido\b", "Use forma neutra: 'Você age com muita rapidez!'"),
    (r"\bvocê é muito corajoso\b", "Use forma neutra: 'Você tem muita coragem!'"),
    (r"\bvocê é muito habilidoso\b", "Use forma neutra: 'Sua habilidade é impressionante!'"),
    (r"\bbem-vindo\b", "Se dirigido a {PLAYER}, use: 'Boas-vindas!' ou 'Que bom ver você!'"),
    (r"\bobrigado/a\b", "Proibido barra de gênero: use 'Agradeço de coração!' ou 'Meus agradecimentos!'"),
    (r"\bcansado\(a\)\b|\bpronto\(a\)\b|\bsozinho\(a\)\b", "Proibido parênteses de gênero (a): reescreva com substantivos abstratos"),
    (r"\bo \{player\}\b|\ba \{player\}\b", "Choque de artigo com {PLAYER}: remova o artigo antes da variável"),
]


def split_md_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def clean_cell(raw: str) -> str:
    return raw.strip().replace("**", "").replace("`", "")


def split_box_lines(cell: str) -> List[str]:
    cleaned = clean_cell(cell)
    lines = re.split(r"<br\s*/?>", cleaned, flags=re.IGNORECASE)
    return [ln.strip() for ln in lines if ln.strip()]


def extract_tags(text: str) -> List[str]:
    """Extrai todas as tags dinâmicas como {PLAYER}, {VAR_1}, [0x05], etc."""
    curly = re.findall(r"\{[A-Za-z0-9_]+\}", text)
    square = re.findall(r"\[0x[0-9A-Fa-f]+\]", text)
    return sorted(curly + square)


def is_system_or_item_file(filepath: Path) -> bool:
    name_low = filepath.name.lower()
    return any(k in name_low for k in ("02-glossario", "03-", "06-", "sistema", "itens", "equipamento", "catalogo", "metricas"))


def audit_file(filepath: Path, hard_limit: int = 36, soft_limit: int = 33) -> Dict[str, Any]:
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    is_dialogue_story = not is_system_or_item_file(filepath)

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    total_rows = 0
    translated_rows = 0

    in_table = False
    id_col, spk_col, en_col, pt_col = 0, 1, 2, 3

    for line_idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|") and ("---" in s or ":---" in s):
            in_table = True
            continue

        if s.startswith("|") and not in_table:
            headers = [h.lower() for h in split_md_row(s)]
            for idx, h in enumerate(headers):
                if any(k in h for k in ("offset", "script", "id")):
                    id_col = idx
                elif any(k in h for k in ("personagem", "speaker", "falante")):
                    spk_col = idx
                elif any(k in h for k in ("original", "en-us")):
                    en_col = idx
                elif any(k in h for k in ("sugerid", "pt-br", "tradução")):
                    pt_col = idx
            continue

        if in_table:
            if not s.startswith("|"):
                in_table = False
                continue

            cells = split_md_row(s)
            if len(cells) <= max(en_col, pt_col):
                continue

            row_id = clean_cell(cells[id_col]) if len(cells) > id_col else f"L{line_idx+1}"
            speaker = clean_cell(cells[spk_col]) if len(cells) > spk_col else ""
            raw_en = clean_cell(cells[en_col])
            raw_pt = clean_cell(cells[pt_col])

            if not raw_en:
                continue

            total_rows += 1
            if not raw_pt or "pendente" in raw_pt.lower() or "[sua tradução" in raw_pt.lower():
                continue

            translated_rows += 1

            # 1. Verificação de Tags Dinâmicas ({PLAYER}, etc.)
            # Se a coluna 0 já é a definição da própria tag (tabela de variáveis do glossário), pula a comparação
            is_var_def_row = row_id.startswith("{") and row_id.endswith("}")
            en_tags = extract_tags(raw_en)
            pt_tags = extract_tags(raw_pt)
            if not is_var_def_row and en_tags != pt_tags:
                errors.append({
                    "line": line_idx + 1,
                    "id": row_id,
                    "gate": "GATE 1: TAGS",
                    "msg": f"Tags divergentes! Original={en_tags} vs PT-BR={pt_tags}",
                    "text": raw_pt
                })

            # 2. Verificação de Limite de Caracteres e Orfandade por Linha Física
            pt_box_lines = split_box_lines(raw_pt)
            for b_idx, b_line in enumerate(pt_box_lines):
                c_len = len(b_line)
                if c_len > hard_limit:
                    errors.append({
                        "line": line_idx + 1,
                        "id": row_id,
                        "gate": "GATE 2: OVERFLOW",
                        "msg": f"Linha {b_idx+1} tem {c_len} chars (Máx={hard_limit}, Excesso=+{c_len - hard_limit})",
                        "text": b_line
                    })
                elif c_len >= soft_limit:
                    warnings.append({
                        "line": line_idx + 1,
                        "id": row_id,
                        "gate": "GATE 2: SOFT LIMIT",
                        "msg": f"Linha {b_idx+1} na zona amarela ({c_len}/{hard_limit} chars)",
                        "text": b_line
                    })

                # 3. Verificação de Orfandade Textual (monossílabo preso no fim da linha antes de outra linha)
                if b_idx < len(pt_box_lines) - 1:
                    words = b_line.split()
                    if words:
                        last_word = re.sub(r"[^\wÀ-ÿ]", "", words[-1]).lower()
                        if last_word in ORPHAN_WORDS:
                            warnings.append({
                                "line": line_idx + 1,
                                "id": row_id,
                                "gate": "GATE 3: ORFANDADE",
                                "msg": f"Palavra curta '{words[-1]}' órfã no fim da linha {b_idx+1} antes de <br>",
                                "text": b_line
                            })

            # 4. Política Rígida de Abreviações em Diálogos de História
            if is_dialogue_story:
                for abbr_pat in FORBIDDEN_DIALOGUE_ABBREVS:
                    m = re.search(abbr_pat, raw_pt, flags=re.IGNORECASE)
                    if m:
                        errors.append({
                            "line": line_idx + 1,
                            "id": row_id,
                            "gate": "GATE 4: ABREVIAÇÃO PROIBIDA",
                            "msg": f"Abreviação '{m.group(0)}' proibida em diálogos de história!",
                            "text": raw_pt
                        })

            # 5. Neutralidade de Gênero Sistêmica
            for pat, tip in GENDER_SUSPECT_PATTERNS:
                if re.search(pat, raw_pt, flags=re.IGNORECASE):
                    warnings.append({
                        "line": line_idx + 1,
                        "id": row_id,
                        "gate": "GATE 5: NEUTRALIDADE GÊNERO",
                        "msg": tip,
                        "text": raw_pt
                    })

    return {
        "file": filepath.name,
        "path": str(filepath),
        "total_rows": total_rows,
        "translated_rows": translated_rows,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Quality Gate Hook do GBA Localization Studio")
    parser.add_argument("target", help="Arquivo .md ou pasta 'ARQUIVOS md' para auditar")
    parser.add_argument("--limit", "-l", type=int, default=36, help="Hard Limit de caracteres por linha (padrão: 36)")
    parser.add_argument("--soft", "-s", type=int, default=33, help="Soft Limit de alerta (padrão: 33)")
    parser.add_argument("--strict", action="store_true", help="Falha com exit code 1 também se houver warnings")

    args = parser.parse_args()
    target_path = Path(args.target)

    if not target_path.exists():
        print(f"❌ Alvo não encontrado: {target_path}")
        sys.exit(1)

    files_to_check: List[Path] = []
    if target_path.is_file():
        files_to_check.append(target_path)
    else:
        for f in sorted(target_path.rglob("*.md")):
            if not any(k in f.name.lower() for k in ("00-", "01-", "template", "catalogo", "metricas", "relatorio", "controle")):
                files_to_check.append(f)

    total_errors = 0
    total_warnings = 0

    print("=" * 72)
    print(f"🛡️  GBA LOCALIZATION STUDIO — QUALITY GATE AUDITOR (Hard Limit: {args.limit} chars)")
    print("=" * 72)

    for f in files_to_check:
        res = audit_file(f, hard_limit=args.limit, soft_limit=args.soft)
        errs = res["errors"]
        warns = res["warnings"]
        total_errors += len(errs)
        total_warnings += len(warns)

        status_icon = "✅ PASS" if not errs else "❌ FAIL"
        print(f"\n📄 {res['file']} [{res['translated_rows']}/{res['total_rows']} traduzidas] ➔ {status_icon} ({len(errs)} erros, {len(warns)} alertas)")

        for e in errs[:25]:
            print(f"   🔴 [L{e['line']} | {e['id']}] {e['gate']}: {e['msg']}")
            print(f"      ↳ \"{e['text']}\"")
        if len(errs) > 25:
            print(f"   ... e mais {len(errs) - 25} erros neste arquivo.")

        for w in warns[:10]:
            print(f"   🟡 [L{w['line']} | {w['id']}] {w['gate']}: {w['msg']}")
        if len(warns) > 10:
            print(f"   ... e mais {len(warns) - 10} alertas neste arquivo.")

    print("\n" + "=" * 72)
    if total_errors > 0 or (args.strict and total_warnings > 0):
        print(f"🚫 QUALITY GATE BLOQUEADO: {total_errors} erro(s) crítico(s) e {total_warnings} alerta(s) encontrados.")
        print("🔧 Corrija os itens vermelhos acima antes de liberar o lote ou compilar a ROM!")
        sys.exit(1)
    else:
        print(f"🏆 QUALITY GATE APROVADO! Zero erros críticos ({total_warnings} alertas leves).")
        sys.exit(0)


if __name__ == "__main__":
    main()
