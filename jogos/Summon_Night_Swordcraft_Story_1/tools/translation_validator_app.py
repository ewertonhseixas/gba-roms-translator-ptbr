#!/usr/bin/env python3
"""
Validador e Editor Interativo de Tradução (PT-BR)
Summon Night: Swordcraft Story (GBA)
=================================================
Servidor local (zero dependências externas) que lê e atualiza diretamente
os arquivos .md da pasta "ARQUIVOS md/", permitindo:
  - Selecionar a categoria (arquivo .md) e filtrar por seção/status/busca
  - Visualizar o texto original em EN-US, o contexto (endereço ROM, personagem,
    seção, observações), a tradução sugerida em PT-BR e a opção alternativa (se houver)
  - Editar livremente a tradução (incluindo Nome + Descrição para armas/itens/magias)
  - Confirmar a tradução com 1 clique (ou Ctrl+Enter), salvando direto na linha
    correspondente do arquivo .md e marcando como "✅ Validado".
"""

import json
import os
import re
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

ROOT_DIR = Path(__file__).resolve().parent.parent
MD_DIR = ROOT_DIR / "ARQUIVOS md"
UI_HTML_PATH = Path(__file__).resolve().parent / "validator_ui.html"
EMBEDDED_JS_PATH = Path(__file__).resolve().parent / "embedded_md_data.js"

# Regex para extrair alternativa inline do tipo: `Texto A` *(ou `Texto B`)* / *(ou Texto B)*
INLINE_OPT_RE = re.compile(
    r"^(.*?)\s*\*?\(\s*ou\s+([^)]+?)\s*\)\*?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def split_md_row(line: str) -> List[str]:
    """Divide uma linha de tabela Markdown '| a | b | c |' nas células internas."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def join_md_row(cells: List[str]) -> str:
    """Reconstrói uma linha de tabela Markdown formatada."""
    return "| " + " | ".join(cells) + " |"


def clean_cell_to_text(raw: str) -> Tuple[str, str, str]:
    """
    Converte o conteúdo bruto de uma célula Markdown em:
      (texto_principal_limpo, alternativa_inline_limpa, nota_extra)
    Exemplo:
      '`Maninho` / `Maninha` *(ou `Irmãozão` / `Irmãzona`)*'
      -> ('Maninho / Maninha', 'Irmãozão / Irmãzona', '')
    """
    s = raw.strip()
    opt_text = ""

    m = INLINE_OPT_RE.match(s)
    if m:
        s = m.group(1).strip()
        opt_raw = m.group(2).strip()
        opt_text = _strip_md_formatting(opt_raw)

    main_text = _strip_md_formatting(s)
    return main_text, opt_text, ""


def _strip_md_formatting(s: str) -> str:
    """Converte `<br>` em quebra de linha real e remove crases/negritos de formatação Markdown."""
    parts = re.split(r"<br\s*/?>", s, flags=re.IGNORECASE)
    cleaned_lines = []
    for p in parts:
        p = p.strip()
        p = p.replace("**", "").replace("`", "").strip()
        cleaned_lines.append(p)
    return "\n".join(cleaned_lines)


def text_to_md_cell(text: str, use_backticks: bool = True) -> str:
    """
    Converte o texto editado pelo usuário (com quebras de linha '\n') de volta
    para o formato da célula Markdown (`linha 1`<br>`linha 2`).
    """
    lines = [ln.replace("|", "/").rstrip("\r") for ln in text.split("\n")]
    if not lines:
        return ""
    if use_backticks:
        return "<br>".join(f"`{ln}`" if ln else "" for ln in lines)
    else:
        return "<br>".join(f"**{ln}**" if ln else "" for ln in lines)


def classify_table_columns(headers: List[str]) -> Optional[Dict[str, Any]]:
    """
    Analisa os nomes das colunas do cabeçalho da tabela Markdown e retorna
    o mapeamento semântico das colunas.
    """
    h_lower = [h.lower() for h in headers]

    # Ignora tabelas que não são de tradução (ex: tabelas técnicas em 00/01 se houver)
    has_en = any("original" in h or "en-us" in h or "padrão" in h for h in h_lower)
    has_pt = any("sugerid" in h or "pt-br" in h or "tradução" in h for h in h_lower)
    if not (has_en and has_pt):
        return None

    mapping: Dict[str, Any] = {
        "id_col": None,
        "en_col": None,
        "en_desc_col": None,
        "pt_col": None,
        "pt_desc_col": None,
        "opt_col": None,
        "context_cols": [],
        "status_col": None,
    }

    for idx, h in enumerate(h_lower):
        if "status" in h or "validado" in h:
            mapping["status_col"] = idx
        elif ("descrição original" in h) or ("desc" in h and "original" in h):
            mapping["en_desc_col"] = idx
        elif ("descrição sugerida" in h) or ("desc" in h and "sugerid" in h):
            mapping["pt_desc_col"] = idx
        elif "original" in h or "en-us" in h or "padrão (en" in h:
            if mapping["en_col"] is None:
                mapping["en_col"] = idx
        elif "alternativa" in h or "opção b" in h:
            mapping["opt_col"] = idx
        elif "sugerid" in h or "pt-br" in h or "tradução" in h:
            if mapping["pt_col"] is None:
                mapping["pt_col"] = idx
        elif any(k in h for k in ("endereço", "offset", "tag no script", "script / offset")):
            if mapping["id_col"] is None:
                mapping["id_col"] = idx
            else:
                mapping["context_cols"].append(idx)
        else:
            mapping["context_cols"].append(idx)

    if mapping["en_col"] is None or mapping["pt_col"] is None:
        return None

    return mapping


def list_translation_md_files() -> List[Dict[str, Any]]:
    """Lista todos os arquivos .md de tradução (na raiz e subpastas de ARQUIVOS md) com estatísticas."""
    files = sorted(MD_DIR.rglob("*.md"), key=lambda p: (p.name, p.as_posix()))
    result = []
    for f in files:
        if f.name.startswith(("00-", "01-")):
            continue
        rel_name = f.relative_to(MD_DIR).as_posix()
        parsed = parse_md_file(f)
        entries = parsed["entries"]
        total = len(entries)
        validated = sum(1 for e in entries if e["validated"])
        result.append({
            "filename": rel_name,
            "title": parsed["title"] or f.stem,
            "total": total,
            "validated": validated,
        })
    return result


def canonicalize_character(raw_name: str) -> Tuple[str, str]:
    """
    Normaliza um nome de personagem bruto extraído de tabelas/contexto.
    Retorna (id_canônico, nome_exibição).
    """
    if not raw_name:
        return "geral", "Cena / Geral"
    
    clean = re.sub(r"\(.*?\)", "", raw_name).strip()
    c_lower = clean.lower()

    if any(k in c_lower for k in ("protagonista", "cleru", "pratty", "{player}", "protagonist")):
        return "protagonist", "Protagonista (Cleru / Pratty)"
    if any(k in c_lower for k in ("amariss", "mãe", "mother")):
        return "amariss", "Amariss (Mãe)"
    if any(k in c_lower for k in ("mestre bron", "bron", "master bron")):
        return "bron", "Mestre Bron"
    if "rasho" in c_lower:
        return "rasho", "Rasho"
    if "sanary" in c_lower:
        return "sanary", "Sanary"
    if "sugar" in c_lower:
        return "sugar", "Sugar"
    if "kutty" in c_lower:
        return "kutty", "Kutty"
    if "zantek" in c_lower:
        return "zantek", "Zantek"
    if "chaves" in c_lower:
        return "chaves", "Chaves"
    if "kenon" in c_lower:
        return "kenon", "Kenon"
    if "razzy" in c_lower:
        return "razzy", "Razzy"
    if "ariel" in c_lower:
        return "ariel", "Ariel"
    if "varil" in c_lower:
        return "varil", "Varil"
    if "sakuro" in c_lower:
        return "sakuro", "Sakuro (Lord Safira)"
    if "kouren" in c_lower:
        return "kouren", "Kouren (Lorde Rubi)"
    if any(k in c_lower for k in ("shintetsu", "pai", "father")):
        return "shintetsu", "Shintetsu (Pai)"
    if "lynn" in c_lower:
        return "lynn", "Lynn"
    if "blaire" in c_lower:
        return "blaire", "Blaire"
    if "zeed" in c_lower:
        return "zeed", "Zeed"
    if "parista" in c_lower:
        return "parista", "Parista"
    if any(k in c_lower for k in ("sistema", "aviso", "tela", "menu", "status", "system")):
        return "system", "Sistema / Narração"
    if any(k in c_lower for k in ("escolha", "choice")):
        return "choice", "Escolha do Jogador"

    c_name = clean.title() if clean.islower() else clean
    return clean.lower().replace(" ", "_"), c_name


def enrich_entries(entries: List[Dict[str, Any]], doc_title: str) -> List[Dict[str, Any]]:
    """
    Enriquece as entradas identificando Falante, Destinatário, se é Pensamento,
    Script Group e estatísticas completas de personagens da cena.
    """
    if not entries:
        return []

    # 1ª Passada: detecta Script Group e Falante Bruto
    for idx, e in enumerate(entries):
        ref_id = e.get("ref_id", "")
        sec = e.get("section", "")
        ctx = e.get("context", "")
        en = e.get("en_text", "")
        pt = e.get("pt_text", "")

        # Grupo de Script / Cena
        m_scr = re.search(r"#(\d+)", ref_id) or re.search(r"#(\d+)", sec)
        if m_scr:
            s_group = f"Script #{m_scr.group(1)}"
        elif sec:
            s_group = sec.split("›")[0].strip()
        else:
            s_group = doc_title or "Geral"
        e["script_group"] = s_group

        # Extrai falante bruto
        raw_speaker = ""
        m_ctx = re.search(r"Personagem(?:\s*/\s*Contexto)?:\s*([^|]+)", ctx, re.I)
        if m_ctx:
            raw_speaker = m_ctx.group(1).strip()
        elif "Falante:" in ctx:
            raw_speaker = ctx.split("Falante:")[1].split("|")[0].strip()
        else:
            # Verifica tag embutida no texto tipo *(Protagonista:)*
            m_text = re.search(r"\*\(([^:)]+):?\)\*", en) or re.search(r"\*\(([^:)]+):?\)\*", pt)
            if m_text:
                raw_speaker = m_text.group(1).strip()
            elif any(k in sec.lower() for k in ("mestre bron", "amariss", "sugar", "rasho", "sanary", "kutty", "chaves")):
                for k in ("mestre bron", "amariss", "sugar", "rasho", "sanary", "kutty", "chaves"):
                    if k in sec.lower():
                        raw_speaker = k.title()
                        break
            elif any(k in doc_title.lower() for k in ("interface", "menu", "armas", "itens", "bestiário")):
                raw_speaker = "Sistema"
            else:
                raw_speaker = "Geral"

        s_id, s_name = canonicalize_character(raw_speaker)
        e["speaker_raw"] = raw_speaker
        e["speaker"] = s_name
        e["speaker_id"] = s_id

        # Pensamento / Monólogo
        clean_en = en.strip()
        is_thought = (clean_en.startswith("(") and clean_en.endswith(")")) or "(Pensamento)" in ctx or "(Monólogo)" in ctx
        e["is_thought"] = is_thought

    # 2ª Passada: Agrupa por script_group e infere Destinatário
    groups: Dict[str, List[int]] = {}
    for idx, e in enumerate(entries):
        groups.setdefault(e["script_group"], []).append(idx)

    for s_group, indices in groups.items():
        # Coleta participantes não-sistema e não-escolha da cena
        participants = []
        for i in indices:
            sp_id = entries[i]["speaker_id"]
            if sp_id not in ("system", "choice", "geral") and sp_id not in participants:
                participants.append(sp_id)

        last_non_self_speaker_id: Optional[str] = None
        last_speaker_id: Optional[str] = None

        for i in indices:
            e = entries[i]
            sp_id = e["speaker_id"]
            ctx = e.get("context", "")
            en_lower = e.get("en_text", "").lower()
            pt_lower = e.get("pt_text", "").lower()

            target_name = ""
            target_id = ""

            if e["is_thought"]:
                target_name = "💭 Pensamento (Monólogo)"
                target_id = "thought"
            elif "(c/ rasho)" in ctx.lower():
                target_id, target_name = canonicalize_character("Rasho")
            elif "(c/ sanary)" in ctx.lower():
                target_id, target_name = canonicalize_character("Sanary")
            elif "(c/ sugar)" in ctx.lower():
                target_id, target_name = canonicalize_character("Sugar")
            elif "(c/ kutty)" in ctx.lower():
                target_id, target_name = canonicalize_character("Kutty")
            elif any(w in en_lower[:30] or w in pt_lower[:30] for w in ("mother", "mãe", "mamãe")) and sp_id != "amariss":
                target_id, target_name = canonicalize_character("Amariss")
            elif any(w in en_lower[:30] or w in pt_lower[:30] for w in ("master bron", "mestre bron")) and sp_id != "bron":
                target_id, target_name = canonicalize_character("Mestre Bron")
            elif "sugar" in en_lower[:30] and sp_id != "sugar":
                target_id, target_name = canonicalize_character("Sugar")
            elif "rasho" in en_lower[:30] and sp_id != "rasho":
                target_id, target_name = canonicalize_character("Rasho")
            elif "sanary" in en_lower[:30] and sp_id != "sanary":
                target_id, target_name = canonicalize_character("Sanary")
            elif "kutty" in en_lower[:30] and sp_id != "kutty":
                target_id, target_name = canonicalize_character("Kutty")
            elif sp_id == "system":
                target_name = "Jogador"
                target_id = "player"
            elif sp_id == "choice":
                target_name = "Interlocutor da Cena"
                target_id = "interlocutor"
            else:
                # Se mudou de falante, o destinatário é o anterior!
                if last_speaker_id and last_speaker_id != sp_id and last_speaker_id not in ("system", "choice"):
                    target_id, target_name = canonicalize_character(last_speaker_id)
                # Se o mesmo falante continua falando
                elif last_non_self_speaker_id and last_non_self_speaker_id != sp_id:
                    target_id, target_name = canonicalize_character(last_non_self_speaker_id)
                # Se há exatamente 2 participantes na cena
                elif len(participants) == 2:
                    other_id = participants[1] if participants[0] == sp_id else participants[0]
                    target_id, target_name = canonicalize_character(other_id)
                elif len(participants) > 1 and sp_id != "protagonist":
                    # Maioria dos NPCs fala com o Protagonista
                    target_id, target_name = canonicalize_character("Protagonista")
                else:
                    target_name = "Cena / Todos"
                    target_id = "geral"

            e["addressee"] = target_name
            e["addressee_id"] = target_id

            if sp_id not in ("system", "choice"):
                if last_speaker_id and last_speaker_id != sp_id:
                    last_non_self_speaker_id = last_speaker_id
                last_speaker_id = sp_id

    # 3ª Passada: Monta lista consolidada de personagens para os filtros
    char_map: Dict[str, Dict[str, Any]] = {}
    for e in entries:
        s_id = e["speaker_id"]
        s_name = e["speaker"]
        if s_id not in char_map:
            char_map[s_id] = {"id": s_id, "name": s_name, "spoken": 0, "addressed": 0, "total": 0}
        char_map[s_id]["spoken"] += 1
        char_map[s_id]["total"] += 1

        t_id = e["addressee_id"]
        t_name = e["addressee"]
        if t_id and t_id not in ("thought", "geral", "player", "interlocutor"):
            if t_id not in char_map:
                char_map[t_id] = {"id": t_id, "name": t_name, "spoken": 0, "addressed": 0, "total": 0}
            char_map[t_id]["addressed"] += 1
            char_map[t_id]["total"] += 1

    sorted_chars = sorted(char_map.values(), key=lambda c: (c["total"], c["spoken"]), reverse=True)
    return sorted_chars


def parse_md_file(filepath: Path) -> Dict[str, Any]:
    """
    Lê um arquivo .md e extrai todas as linhas de tabelas de tradução,
    preservando o número exato da linha (`line_index`) para gravação direta.
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    doc_title = ""
    current_h2 = ""
    current_h3 = ""
    entries: List[Dict[str, Any]] = []

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].strip()

        if line.startswith("# ") and not doc_title:
            doc_title = line[2:].strip()
            i += 1
            continue
        if line.startswith("## "):
            current_h2 = line[3:].strip()
            current_h3 = ""
            i += 1
            continue
        if line.startswith("### "):
            current_h3 = line[4:].strip()
            i += 1
            continue

        # Detecta início de tabela Markdown
        if line.startswith("|") and (i + 1 < n) and re.match(r"^\|\s*:?---", lines[i + 1].strip()):
            header_line_idx = i
            sep_line_idx = i + 1
            headers = split_md_row(lines[header_line_idx])
            col_map = classify_table_columns(headers)

            i += 2
            if col_map is None:
                while i < n and lines[i].strip().startswith("|"):
                    i += 1
                continue

            while i < n and lines[i].strip().startswith("|"):
                row_cells = split_md_row(lines[i])
                # Garante que a linha tem células suficientes
                while len(row_cells) < len(headers):
                    row_cells.append("")

                en_raw = row_cells[col_map["en_col"]]
                pt_raw = row_cells[col_map["pt_col"]]

                en_text, _, _ = clean_cell_to_text(en_raw)
                pt_text, inline_opt, _ = clean_cell_to_text(pt_raw)

                en_desc = ""
                pt_desc = ""
                if col_map["en_desc_col"] is not None and col_map["en_desc_col"] < len(row_cells):
                    en_desc, _, _ = clean_cell_to_text(row_cells[col_map["en_desc_col"]])
                if col_map["pt_desc_col"] is not None and col_map["pt_desc_col"] < len(row_cells):
                    pt_desc, _, _ = clean_cell_to_text(row_cells[col_map["pt_desc_col"]])

                opt_text = inline_opt
                if col_map["opt_col"] is not None and col_map["opt_col"] < len(row_cells):
                    col_opt_clean, _, _ = clean_cell_to_text(row_cells[col_map["opt_col"]])
                    if col_opt_clean:
                        opt_text = col_opt_clean

                ref_id = ""
                if col_map["id_col"] is not None and col_map["id_col"] < len(row_cells):
                    ref_id = _strip_md_formatting(row_cells[col_map["id_col"]])

                ctx_parts = []
                for c_idx in col_map["context_cols"]:
                    if c_idx < len(row_cells) and row_cells[c_idx].strip():
                        col_label = headers[c_idx]
                        val_clean = _strip_md_formatting(row_cells[c_idx])
                        ctx_parts.append(f"{col_label}: {val_clean}")

                section_label = current_h2
                if current_h3:
                    section_label = f"{current_h2} › {current_h3}"

                validated = False
                status_str = "⏳ Pendente"
                if col_map["status_col"] is not None and col_map["status_col"] < len(row_cells):
                    st_cell = row_cells[col_map["status_col"]]
                    if "✅" in st_cell or "validado" in st_cell.lower() or "[x]" in st_cell.lower():
                        validated = True
                        status_str = "✅ Validado"

                use_bold = pt_raw.strip().startswith("**")

                entries.append({
                    "line_index": i,
                    "header_line_index": header_line_idx,
                    "sep_line_index": sep_line_idx,
                    "section": section_label,
                    "ref_id": ref_id,
                    "context": " | ".join(ctx_parts) if ctx_parts else section_label,
                    "en_text": en_text,
                    "en_desc": en_desc,
                    "pt_text": pt_text,
                    "pt_desc": pt_desc,
                    "opt_text": opt_text,
                    "has_desc": col_map["pt_desc_col"] is not None,
                    "validated": validated,
                    "status_str": status_str,
                    "use_bold": use_bold,
                })
                i += 1
            continue

        i += 1

    characters = enrich_entries(entries, doc_title)

    rel_name = filepath.relative_to(MD_DIR).as_posix() if filepath.is_relative_to(MD_DIR) else filepath.name
    return {
        "filename": rel_name,
        "title": doc_title,
        "entries": entries,
        "characters": characters,
    }


def update_md_entry(
    filepath: Path,
    line_index: int,
    new_pt_text: str,
    new_pt_desc: Optional[str],
    validated: bool,
) -> Dict[str, Any]:
    """
    Atualiza diretamente a linha `line_index` no arquivo `.md`, salvando o texto
    PT-BR editado e adicionando/atualizando a coluna `| Status |` com `✅ Validado`
    (ou `⏳ Pendente`).
    """
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not (0 <= line_index < len(lines)):
        raise ValueError(f"Linha inválida: {line_index}")

    # Encontra o cabeçalho da tabela à qual esta linha pertence
    h_idx = line_index - 1
    while h_idx >= 0 and lines[h_idx].strip().startswith("|"):
        h_idx -= 1
    header_line_idx = h_idx + 1
    sep_line_idx = header_line_idx + 1

    headers = split_md_row(lines[header_line_idx])
    col_map = classify_table_columns(headers)
    if col_map is None:
        raise ValueError("Não foi possível identificar as colunas da tabela.")

    # Se a tabela ainda não possui coluna "Status", adiciona no cabeçalho, separador e todas as linhas da tabela!
    if col_map["status_col"] is None:
        headers.append("Status")
        lines[header_line_idx] = join_md_row(headers)

        sep_cells = split_md_row(lines[sep_line_idx])
        sep_cells.append(":---:")
        lines[sep_line_idx] = join_md_row(sep_cells)

        r_idx = sep_line_idx + 1
        while r_idx < len(lines) and lines[r_idx].strip().startswith("|"):
            r_cells = split_md_row(lines[r_idx])
            while len(r_cells) < len(headers) - 1:
                r_cells.append("")
            r_cells.append("⏳ Pendente")
            lines[r_idx] = join_md_row(r_cells)
            r_idx += 1

        col_map["status_col"] = len(headers) - 1

    # Agora atualiza a linha específica
    row_cells = split_md_row(lines[line_index])
    while len(row_cells) < len(headers):
        row_cells.append("")

    pt_col = col_map["pt_col"]
    old_pt_raw = row_cells[pt_col].strip()
    use_backticks = not old_pt_raw.startswith("**")

    # Preserva a alternativa inline *(ou ...)* se o usuário não quiser perdê-la?
    # Não: ao confirmar, salvamos o texto escolhido limpo na coluna PT-BR!
    row_cells[pt_col] = text_to_md_cell(new_pt_text, use_backticks=use_backticks)

    if col_map["pt_desc_col"] is not None and new_pt_desc is not None:
        row_cells[col_map["pt_desc_col"]] = text_to_md_cell(new_pt_desc, use_backticks=True)

    status_col = col_map["status_col"]
    row_cells[status_col] = "✅ Validado" if validated else "⏳ Pendente"

    lines[line_index] = join_md_row(row_cells)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    export_embedded_js()

    return {
        "ok": True,
        "line_index": line_index,
        "validated": validated,
        "status_str": row_cells[status_col],
    }


def export_embedded_js() -> None:
    """
    Gera o arquivo `tools/embedded_md_data.js` com todos os arquivos .md já
    parseados para que `validator_ui.html` funcione instantaneamente mesmo se
    aberto direto via `file:///...`.
    """
    files = sorted(MD_DIR.rglob("*.md"), key=lambda p: (p.name, p.as_posix()))
    cats = []
    files_map = {}
    for f in files:
        if f.name.startswith(("00-", "01-")):
            continue
        rel_name = f.relative_to(MD_DIR).as_posix()
        parsed = parse_md_file(f)
        entries = parsed["entries"]
        total = len(entries)
        validated = sum(1 for e in entries if e["validated"])
        cats.append({
            "filename": rel_name,
            "title": parsed["title"] or f.stem,
            "total": total,
            "validated": validated,
        })
        files_map[rel_name] = parsed

    payload = {"categories": cats, "files": files_map}
    js_content = "window.EMBEDDED_MD_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    EMBEDDED_JS_PATH.write_text(js_content, encoding="utf-8")


class ValidatorRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
        # Silencia logs excessivos no terminal
        pass

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data: Any, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            html_bytes = UI_HTML_PATH.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(html_bytes)
            return

        if parsed.path == "/embedded_md_data.js":
            if not EMBEDDED_JS_PATH.is_file():
                export_embedded_js()
            js_bytes = EMBEDDED_JS_PATH.read_bytes()
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Content-Length", str(len(js_bytes)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(js_bytes)
            return

        if parsed.path == "/api/categories":
            cats = list_translation_md_files()
            self._send_json({"categories": cats})
            return

        if parsed.path == "/api/file":
            qs = parse_qs(parsed.query)
            fname = qs.get("name", [""])[0]
            fpath = (MD_DIR / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(MD_DIR.resolve()):
                self._send_json({"error": "Arquivo não encontrado."}, status=404)
                return
            data = parse_md_file(fpath)
            self._send_json(data)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/save":
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body)

            fname = payload.get("filename", "")
            line_index = int(payload.get("line_index", -1))
            pt_text = payload.get("pt_text", "")
            pt_desc = payload.get("pt_desc", None)
            validated = bool(payload.get("validated", True))

            fpath = (MD_DIR / fname).resolve()
            if not fpath.is_file() or not fpath.is_relative_to(MD_DIR.resolve()):
                self._send_json({"error": "Arquivo inválido."}, status=400)
                return

            try:
                res = update_md_entry(fpath, line_index, pt_text, pt_desc, validated)
                self._send_json(res)
            except Exception as exc:
                self._send_json({"error": str(exc)}, status=500)
            return

        self._send_json({"error": "Rota não encontrada."}, status=404)


def main() -> int:
    export_embedded_js()
    port = int(os.environ.get("VALIDATOR_PORT", "8765"))
    no_browser = "--no-browser" in sys.argv

    server = ThreadingHTTPServer(("127.0.0.1", port), ValidatorRequestHandler)
    url = f"http://127.0.0.1:{port}"
    print("=" * 72)
    print(" VALIDADOR DE TRADUÇÃO GBA — SUMMON NIGHT: SWORDCRAFT STORY")
    print("=" * 72)
    print(f" • Pasta monitorada : {MD_DIR}")
    print(f" • Acesse no browser: {url}")
    print("=" * 72)

    if not no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
