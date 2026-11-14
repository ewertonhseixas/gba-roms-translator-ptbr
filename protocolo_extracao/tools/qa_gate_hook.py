#!/usr/bin/env python3
"""
QA Gate Hook — GBA Localization Studio (Protocolo Mestre de Tradução)
=====================================================================
Inspirado nos Quality Gates do Claude-Code-Game-Studios.
Executa uma auditoria implacável em 5 barreiras sobre arquivos Markdown (.md)
de tradução antes de liberar para compilação na ROM:

  1. [SINTAXE & VARIÁVEIS] Tags {PLAYER}, {PARTNER}, {SIBLING}, {MASTER} preservadas
     (suporta caixas de diálogo multi-linha consecutivas onde a tag foi movida para a linha vizinha).
  2. [BARREIRA ANTI-OVERFLOW] Nenhuma linha física acima do Hard Limit (padrão: 35 chars)
     e alerta no Soft Limit (33-35 chars).
  3. [ORFANDADE TEXTUAL] Detecta monossílabos órfãos ('o', 'a', 'de', 'em', 'e', 'que')
     isolados no fim de uma linha antes de <br>.
  4. [POLÍTICA DE ABREVIAÇÕES] Bloqueia internetês ou abreviações ('vc', 'tb', 'pq', 'atq.', 'esp.')
     em arquivos de diálogo de história (ignorando gagueiras legítimas como 'Q-Qual').
  5. [GLOSSÁRIO, INGLÊS RESIDUAL & NEUTRALIDADE] Audita frases não traduzidas ("⏳ Pendente"),
     inglês residual óbvio e adjetivos marcados no masculino em falas de {PLAYER}.
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Abreviações proibidas em diálogos de história (permitidas apenas em 03..07: sistema, armas, itens, bestiário)
# Nota: evita casar letras seguidas de hífen de gagueira (ex: "Q-Qual", "P-Por") usando (?!-)
FORBIDDEN_DIALOGUE_ABBREVS = [
    r"(?<!-)\bvc\b(?!-)", r"(?<!-)\bvcs\b(?!-)", r"(?<!-)\bpq\b(?!-)",
    r"(?<!-)\btb\b(?!-)", r"(?<!-)\btbm\b(?!-)", r"(?<!-)\bctz\b(?!-)",
    r"(?<!-)\bblz\b(?!-)", r"(?<!-)\bvlw\b(?!-)", r"(?<!-)\bflw\b(?!-)",
    r"(?<!-)\bq\b(?!-)", r"\bp/\b", r"\bc/\b",
    r"\batq\.", r"\bdef\.", r"\brecup\.", r"\besp\.", r"\bmin\.", r"\belem\."
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
    (r"\bo \{player\}\b|\ba \{player\}\b|\bdo \{player\}\b|\bda \{player\}\b|\bao \{player\}\b|\bpelo \{player\}\b", "Choque de artigo com {PLAYER}: remova o artigo masculino/feminino antes da variável"),
]

# Palavras em inglês residual que não deveriam aparecer soltas no texto PT-BR
RESIDUAL_ENGLISH_PATTERNS = [
    r"\bCraftknight\b", r"\bCraftlord\b", r"\bSummon Beast\b", r"\bGuardian Beast\b",
    r"\bSummon Stray\b", r"\bSilver Guild\b", r"\bGold Guild\b", r"\bCentral Tower\b",
    r"\bMarine Dungeon\b", r"\bBosque Labyrinth\b", r"\bKagro Volcano\b",
    r"\bHuh\?", r"\bSigh\b", r"\bGulp\b", r"\bYikes\b"
]


def split_md_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def clean_cell(raw: str) -> str:
    s = raw.strip()
    # Remove notas editoriais fora das crases se houver crases (ex: `Axe forged...` *(erro no original)*)
    s = re.sub(r"\*\([^)]+\)\*", "", s).strip()
    return s.replace("**", "").replace("`", "").strip()


def split_box_lines(cell: str) -> List[str]:
    cleaned = clean_cell(cell)
    lines = re.split(r"<br\s*/?>", cleaned, flags=re.IGNORECASE)
    return [ln.strip() for ln in lines if ln.strip()]


def extract_tags(text: str) -> List[str]:
    """Extrai todas as tags dinâmicas como {PLAYER}, {PARTNER}, [0x05], etc."""
    curly = re.findall(r"\{[A-Za-z0-9_]+\}", text)
    square = re.findall(r"\[0x[0-9A-Fa-f]+\]", text)
    return sorted(curly + square)


def is_glossary_or_reference_file(filepath: Path) -> bool:
    name_low = filepath.name.lower()
    return name_low.startswith(("00-", "01-", "02-")) or any(
        k in name_low for k in ("02-glossario", "catalogo", "metricas", "relatorio", "controle", "template")
    )


def is_system_or_item_file(filepath: Path) -> bool:
    name_low = filepath.name.lower()
    return any(k in name_low for k in ("02-", "03-", "04-", "05-", "06-", "07-", "sistema", "itens", "armas", "bestiario", "equipamento"))


def detect_table_columns(headers: List[str]) -> Optional[Dict[str, Any]]:
    """
    Detecta de forma precisa os pares de colunas (en_col, pt_col) da tabela Markdown.
    Retorna None se for uma tabela puramente explicativa/documental (sem par Original -> Tradução).
    """
    h_low = [h.lower() for h in headers]

    # Caso especial: Tabela de Armas/Itens com 2 pares (Nome Original/Sugerido + Descrição Original/Sugerida)
    name_en, name_pt, desc_en, desc_pt = None, None, None, None
    for idx, h in enumerate(h_low):
        if "nome original" in h:
            name_en = idx
        elif ("nome sugerid" in h or "nome pt-br" in h or "tradução pt-br" in h) and name_pt is None:
            name_pt = idx
        elif "descrição original" in h:
            desc_en = idx
        elif "descrição sugerid" in h or "descrição pt-br" in h:
            desc_pt = idx

    if name_en is not None and name_pt is not None and desc_en is not None and desc_pt is not None:
        return {
            "mode": "dual_item",
            "id_col": 0,
            "pairs": [(name_en, name_pt, 16), (desc_en, desc_pt, 36)],
            "status_col": len(headers) - 1
        }

    # Caso geral: Tabela de Diálogos, UI ou Bestiário (1 par EN -> PT)
    id_col = 0
    spk_col = None
    en_col = None
    pt_col = None
    status_col = None

    for idx, h in enumerate(h_low):
        if any(k in h for k in ("texto original", "nome original", "original (en", "en-us")):
            if en_col is None:
                en_col = idx
        elif any(k in h for k in ("tradução sugerida", "tradução pt-br", "nome sugerido", "sugerida (pt-br)", "pt-br")):
            if pt_col is None and "contexto" not in h and "observa" not in h:
                pt_col = idx
        elif "status" in h:
            status_col = idx
        elif any(k in h for k in ("offset", "script", "id", "endereço")):
            if id_col == 0:
                id_col = idx
        elif any(k in h for k in ("personagem", "speaker", "falante", "opcode")):
            if spk_col is None:
                spk_col = idx

    if en_col is not None and pt_col is not None and en_col != pt_col:
        return {
            "mode": "single",
            "id_col": id_col,
            "spk_col": spk_col,
            "en_col": en_col,
            "pt_col": pt_col,
            "status_col": status_col
        }

    return None


def parse_script_seq_id(row_id: str) -> Optional[Tuple[str, int]]:
    """Extrai (script_id, seq_num) de IDs como '#2213 [18]' ou '#1657 79'."""
    m = re.search(r"(#\d+)\s*\[?(\d+)\]?", row_id)
    if m:
        return (m.group(1), int(m.group(2)))
    return None


def audit_file(filepath: Path, hard_limit: int = 35, soft_limit: int = 33) -> Dict[str, Any]:
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    is_dialogue_story = not is_system_or_item_file(filepath)

    errors: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []
    total_rows = 0
    translated_rows = 0
    untranslated_rows = 0

    col_spec: Optional[Dict[str, Any]] = None
    in_table = False

    # Armazena linhas parseadas da tabela atual para checagem de tags entre linhas consecutivas da mesma caixa
    table_rows: List[Dict[str, Any]] = []

    def flush_table_rows():
        nonlocal total_rows, translated_rows, untranslated_rows
        if not table_rows:
            return

        n = len(table_rows)
        # Pré-verifica tags combinadas em pares/trios consecutivos do mesmo script (quando a frase continua na linha seguinte)
        tag_resolved = [False] * n
        for i in range(n):
            r = table_rows[i]
            if r["en_tags"] == r["pt_tags"]:
                tag_resolved[i] = True

        for i in range(n - 1):
            if not tag_resolved[i] or not tag_resolved[i + 1]:
                s1 = parse_script_seq_id(table_rows[i]["id"])
                s2 = parse_script_seq_id(table_rows[i + 1]["id"])
                if s1 and s2 and s1[0] == s2[0] and abs(s2[1] - s1[1]) <= 2:
                    comb_en = sorted(table_rows[i]["en_tags"] + table_rows[i + 1]["en_tags"])
                    comb_pt = sorted(table_rows[i]["pt_tags"] + table_rows[i + 1]["pt_tags"])
                    if comb_en == comb_pt:
                        tag_resolved[i] = True
                        tag_resolved[i + 1] = True

        for idx, r in enumerate(table_rows):
            total_rows += 1
            raw_en = r["raw_en"]
            raw_pt = r["raw_pt"]
            row_id = r["id"]
            line_no = r["line"]
            row_limit = r["limit"]

            if not raw_pt or "⏳ pendente" in r["status"].lower() or "[sua tradução" in raw_pt.lower():
                untranslated_rows += 1
                errors.append({
                    "line": line_no,
                    "id": row_id,
                    "gate": "GATE 0: PENDENTE",
                    "msg": f"Linha pendente ou sem tradução validada! Original: '{raw_en}'",
                    "text": raw_pt
                })
                continue

            translated_rows += 1

            # 1. Verificação de Tags Dinâmicas ({PLAYER}, etc.)
            if not tag_resolved[idx]:
                errors.append({
                    "line": line_no,
                    "id": row_id,
                    "gate": "GATE 1: TAGS",
                    "msg": f"Tags divergentes! Original={r['en_tags']} vs PT-BR={r['pt_tags']}",
                    "text": raw_pt
                })

            # 2. Verificação de Limite de Caracteres e Orfandade por Linha Física
            pt_box_lines = split_box_lines(raw_pt)
            for b_idx, b_line in enumerate(pt_box_lines):
                c_len = len(b_line)
                if c_len > row_limit:
                    errors.append({
                        "line": line_no,
                        "id": row_id,
                        "gate": "GATE 2: OVERFLOW",
                        "msg": f"Linha {b_idx+1} tem {c_len} chars (Máx={row_limit}, Excesso=+{c_len - row_limit})",
                        "text": b_line
                    })
                elif row_limit == hard_limit and c_len >= soft_limit:
                    warnings.append({
                        "line": line_no,
                        "id": row_id,
                        "gate": "GATE 2: SOFT LIMIT",
                        "msg": f"Linha {b_idx+1} na zona amarela ({c_len}/{row_limit} chars)",
                        "text": b_line
                    })

                # 3. Verificação de Orfandade Textual (apenas quando há múltiplas linhas separadas por <br> na mesma célula)
                if b_idx < len(pt_box_lines) - 1:
                    words = b_line.split()
                    if words:
                        last_word = re.sub(r"[^\wÀ-ÿ]", "", words[-1]).lower()
                        if last_word in ORPHAN_WORDS:
                            warnings.append({
                                "line": line_no,
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
                            "line": line_no,
                            "id": row_id,
                            "gate": "GATE 4: ABREVIAÇÃO PROIBIDA",
                            "msg": f"Abreviação '{m.group(0)}' proibida em diálogos de história!",
                            "text": raw_pt
                        })

            # 5. Neutralidade de Gênero Sistêmica & Inglês Residual
            for pat, tip in GENDER_SUSPECT_PATTERNS:
                if re.search(pat, raw_pt, flags=re.IGNORECASE):
                    warnings.append({
                        "line": line_no,
                        "id": row_id,
                        "gate": "GATE 5: NEUTRALIDADE GÊNERO",
                        "msg": tip,
                        "text": raw_pt
                    })

            for eng_pat in RESIDUAL_ENGLISH_PATTERNS:
                m_eng = re.search(eng_pat, raw_pt)
                if m_eng:
                    warnings.append({
                        "line": line_no,
                        "id": row_id,
                        "gate": "GATE 5: INGLÊS RESIDUAL",
                        "msg": f"Termo em inglês residual detectado: '{m_eng.group(0)}'",
                        "text": raw_pt
                    })

        table_rows.clear()

    for line_idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith("|") and ("---" in s or ":---" in s):
            if col_spec is not None:
                in_table = True
            continue

        if s.startswith("|") and not in_table:
            headers = split_md_row(s)
            col_spec = detect_table_columns(headers)
            continue

        if in_table:
            if not s.startswith("|"):
                flush_table_rows()
                in_table = False
                col_spec = None
                continue

            # Verifica se é uma nova linha de cabeçalho colada sem linha em branco
            cells = split_md_row(s)
            maybe_new_spec = detect_table_columns(cells)
            if maybe_new_spec is not None and any(k in s.lower() for k in ("texto original", "nome original", "endereço rom", "id / offset")):
                flush_table_rows()
                col_spec = maybe_new_spec
                in_table = False
                continue
            if col_spec["mode"] == "dual_item":
                row_id = clean_cell(cells[col_spec["id_col"]]) if len(cells) > col_spec["id_col"] else f"L{line_idx+1}"
                status_val = cells[col_spec["status_col"]] if col_spec["status_col"] < len(cells) else ""
                for en_c, pt_c, lim in col_spec["pairs"]:
                    if len(cells) > max(en_c, pt_c):
                        r_en = clean_cell(cells[en_c])
                        r_pt = clean_cell(cells[pt_c])
                        if r_en:
                            table_rows.append({
                                "line": line_idx + 1,
                                "id": row_id,
                                "raw_en": r_en,
                                "raw_pt": r_pt,
                                "status": status_val,
                                "limit": lim,
                                "en_tags": extract_tags(r_en),
                                "pt_tags": extract_tags(r_pt),
                            })
            else:
                en_c = col_spec["en_col"]
                pt_c = col_spec["pt_col"]
                if len(cells) > max(en_c, pt_c):
                    row_id = clean_cell(cells[col_spec["id_col"]]) if len(cells) > col_spec["id_col"] else f"L{line_idx+1}"
                    status_val = cells[col_spec["status_col"]] if col_spec["status_col"] is not None and col_spec["status_col"] < len(cells) else ""
                    r_en = clean_cell(cells[en_c])
                    r_pt = clean_cell(cells[pt_c])
                    if r_en:
                        is_var_def = row_id.startswith("{") and row_id.endswith("}")
                        table_rows.append({
                            "line": line_idx + 1,
                            "id": row_id,
                            "raw_en": r_en,
                            "raw_pt": r_pt,
                            "status": status_val,
                            "limit": hard_limit,
                            "en_tags": [] if is_var_def else extract_tags(r_en),
                            "pt_tags": [] if is_var_def else extract_tags(r_pt),
                        })

    flush_table_rows()

    return {
        "file": filepath.name,
        "path": str(filepath),
        "total_rows": total_rows,
        "translated_rows": translated_rows,
        "untranslated_rows": untranslated_rows,
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Quality Gate Hook do GBA Localization Studio")
    parser.add_argument("target", help="Arquivo .md ou pasta 'ARQUIVOS md' para auditar")
    parser.add_argument("--limit", "-l", type=int, default=35, help="Hard Limit de caracteres por linha (padrão: 35)")
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
            if not is_glossary_or_reference_file(f):
                files_to_check.append(f)

    total_errors = 0
    total_warnings = 0

    print("=" * 76)
    print(f"🛡️  GBA LOCALIZATION STUDIO — QUALITY GATE AUDITOR (Hard Limit: {args.limit} chars)")
    print("=" * 76)

    for f in files_to_check:
        res = audit_file(f, hard_limit=args.limit, soft_limit=args.soft)
        errs = res["errors"]
        warns = res["warnings"]
        total_errors += len(errs)
        total_warnings += len(warns)

        status_icon = "✅ PASS" if not errs else "❌ FAIL"
        print(f"\n📄 {res['file']} [{res['translated_rows']}/{res['total_rows']} validadas] ➔ {status_icon} ({len(errs)} erros, {len(warns)} alertas)")

        for e in errs[:25]:
            print(f"   🔴 [L{e['line']} | {e['id']}] {e['gate']}: {e['msg']}")
            print(f"      ↳ \"{e['text']}\"")
        if len(errs) > 25:
            print(f"   ... e mais {len(errs) - 25} erros neste arquivo.")

        # Imprime todos os alertas de Gate 3, 4 e 5, e resume Gate 2 (Soft Limit)
        g345 = [w for w in warns if "SOFT LIMIT" not in w["gate"]]
        g2_soft = [w for w in warns if "SOFT LIMIT" in w["gate"]]
        for w in g345:
            print(f"   🟡 [L{w['line']} | {w['id']}] {w['gate']}: {w['msg']}")
            print(f"      ↳ \"{w['text']}\"")
        if g2_soft:
            print(f"   ℹ️  ({len(g2_soft)} linhas na zona amarela de Soft Limit 33-35 chars)")

    print("\n" + "=" * 76)
    if total_errors > 0 or (args.strict and total_warnings > 0):
        print(f"🚫 QUALITY GATE BLOQUEADO: {total_errors} erro(s) crítico(s) e {total_warnings} alerta(s) encontrados.")
        print("🔧 Corrija os itens vermelhos acima antes de liberar o lote ou compilar a ROM!")
        sys.exit(1)
    else:
        print(f"🏆 QUALITY GATE APROVADO! Zero erros críticos ({total_warnings} alertas leves).")
        sys.exit(0)


if __name__ == "__main__":
    main()
