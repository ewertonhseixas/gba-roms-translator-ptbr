#!/usr/bin/env python3
"""
Validador e Editor Interativo de Tradução (PT-BR)
Summon Night: Swordcraft Story 2 (GBA)
=================================================
Servidor local (zero dependências externas) que lê e atualiza diretamente
os arquivos .md da pasta "ARQUIVOS md/", permitindo:
  - Selecionar a categoria (arquivo .md) e filtrar por status/seção/busca
  - Visualizar o texto original em EN-US, script/offset, contexto e tradução PT-BR
  - Editar livremente qualquer linha e confirmar com 1 clique (ou Ctrl+Enter)
  - Botão de Compilar ROM diretamente na interface web
  - Suporte a filtros de "Pendentes", "Traduzidos" e "Validados"
"""

import json
import os
import re
import subprocess
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

INLINE_OPT_RE = re.compile(
    r"^(.*?)\s*\*?\(\s*ou\s+([^)]+?)\s*\)\*?\s*$",
    re.IGNORECASE | re.DOTALL,
)


def split_md_row(line: str) -> List[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def join_md_row(cells: List[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def clean_cell_to_text(raw: str) -> Tuple[str, str, str]:
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
    parts = re.split(r"<br\s*/?>", s, flags=re.IGNORECASE)
    cleaned_lines = []
    for p in parts:
        p = p.strip()
        p = p.replace("**", "").replace("`", "").strip()
        cleaned_lines.append(p)
    return "\n".join(cleaned_lines)


def text_to_md_cell(text: str, use_backticks: bool = False) -> str:
    lines = [ln.replace("|", "/").rstrip("\r") for ln in text.split("\n")]
    if not lines:
        return ""
    if use_backticks:
        return "<br>".join(f"`{ln}`" if ln else "" for ln in lines)
    else:
        return "<br>".join(ln for ln in lines)


def classify_table_columns(headers: List[str]) -> Optional[Dict[str, Any]]:
    h_lower = [h.lower() for h in headers]

    has_en = any("original" in h or "en-us" in h or "padrão" in h for h in h_lower)
    has_pt = any("sugerid" in h or "pt-br" in h or "tradução" in h for h in h_lower)
    if not (has_en and has_pt):
        return None

    mapping: Dict[str, Any] = {
        "id_col": None,
        "script_col": None,
        "offset_col": None,
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
        elif "id script" in h or (h == "script"):
            mapping["script_col"] = idx
        elif "offset" in h:
            mapping["offset_col"] = idx
        elif any(k in h for k in ("endereço", "tag no script", "script / offset")):
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
        translated = sum(1 for e in entries if e.get("is_translated", False))
        result.append({
            "filename": rel_name,
            "title": parsed["title"] or f.stem,
            "total": total,
            "translated": translated,
            "validated": validated,
        })
    return result


def parse_md_file(filepath: Path) -> Dict[str, Any]:
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
                if col_map.get("script_col") is not None and col_map.get("offset_col") is not None:
                    s_id = _strip_md_formatting(row_cells[col_map["script_col"]])
                    off_v = _strip_md_formatting(row_cells[col_map["offset_col"]])
                    ref_id = f"Script {s_id} @ {off_v}"
                elif col_map.get("id_col") is not None and col_map["id_col"] < len(row_cells):
                    ref_id = _strip_md_formatting(row_cells[col_map["id_col"]])
                elif col_map.get("offset_col") is not None and col_map["offset_col"] < len(row_cells):
                    ref_id = _strip_md_formatting(row_cells[col_map["offset_col"]])

                ctx_parts = []
                for c_idx in col_map["context_cols"]:
                    if c_idx < len(row_cells) and row_cells[c_idx].strip():
                        col_label = headers[c_idx]
                        val_clean = _strip_md_formatting(row_cells[c_idx])
                        ctx_parts.append(f"{col_label}: {val_clean}")

                section_label = current_h2
                if current_h3:
                    section_label = f"{current_h2} › {current_h3}"

                is_translated = bool(pt_text.strip())
                validated = False
                status_str = "⏳ Pendente"

                if col_map["status_col"] is not None and col_map["status_col"] < len(row_cells):
                    st_cell = row_cells[col_map["status_col"]]
                    if "✅" in st_cell or "validado" in st_cell.lower() or "[x]" in st_cell.lower():
                        validated = True
                        status_str = "✅ Validado"
                    elif "💬" in st_cell or "traduzido" in st_cell.lower():
                        status_str = "💬 Traduzido"
                    elif is_translated:
                        status_str = "💬 Traduzido"
                    else:
                        status_str = "⏳ Pendente"
                else:
                    if is_translated:
                        status_str = "💬 Traduzido"
                    else:
                        status_str = "⏳ Pendente"

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
                    "is_translated": is_translated,
                    "validated": validated,
                    "status_str": status_str,
                    "use_bold": use_bold,
                })
                i += 1
            continue

        i += 1

    rel_name = filepath.relative_to(MD_DIR).as_posix() if filepath.is_relative_to(MD_DIR) else filepath.name
    return {
        "filename": rel_name,
        "title": doc_title,
        "entries": entries,
    }


def update_md_entry(
    filepath: Path,
    line_index: int,
    new_pt_text: str,
    new_pt_desc: Optional[str],
    validated: bool,
) -> Dict[str, Any]:
    text = filepath.read_text(encoding="utf-8")
    lines = text.splitlines()

    if not (0 <= line_index < len(lines)):
        raise ValueError(f"Linha inválida: {line_index}")

    h_idx = line_index - 1
    while h_idx >= 0 and lines[h_idx].strip().startswith("|"):
        h_idx -= 1
    header_line_idx = h_idx + 1
    sep_line_idx = header_line_idx + 1

    headers = split_md_row(lines[header_line_idx])
    col_map = classify_table_columns(headers)
    if col_map is None:
        raise ValueError("Não foi possível identificar as colunas da tabela.")

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
            if r_idx == line_index:
                r_cells.append("✅ Validado" if validated else "💬 Traduzido")
            else:
                existing_pt = r_cells[col_map["pt_col"]].strip() if col_map["pt_col"] < len(r_cells) else ""
                r_cells.append("💬 Traduzido" if existing_pt else "⏳ Pendente")
            lines[r_idx] = join_md_row(r_cells)
            r_idx += 1

        col_map["status_col"] = len(headers) - 1

    row_cells = split_md_row(lines[line_index])
    while len(row_cells) < len(headers):
        row_cells.append("")

    pt_col = col_map["pt_col"]
    old_pt_raw = row_cells[pt_col].strip()
    use_backticks = old_pt_raw.startswith("`")

    row_cells[pt_col] = text_to_md_cell(new_pt_text, use_backticks=use_backticks)

    if col_map["pt_desc_col"] is not None and new_pt_desc is not None:
        row_cells[col_map["pt_desc_col"]] = text_to_md_cell(new_pt_desc, use_backticks=use_backticks)

    status_col = col_map["status_col"]
    status_label = "✅ Validado" if validated else ("💬 Traduzido" if new_pt_text.strip() else "⏳ Pendente")
    row_cells[status_col] = status_label

    lines[line_index] = join_md_row(row_cells)
    filepath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    export_embedded_js()

    return {
        "ok": True,
        "line_index": line_index,
        "validated": validated,
        "status_str": status_label,
    }


def export_embedded_js() -> None:
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
        translated = sum(1 for e in entries if e.get("is_translated", False))
        cats.append({
            "filename": rel_name,
            "title": parsed["title"] or f.stem,
            "total": total,
            "translated": translated,
            "validated": validated,
        })
        files_map[rel_name] = parsed

    payload = {"categories": cats, "files": files_map}
    js_content = "window.EMBEDDED_MD_DATA = " + json.dumps(payload, ensure_ascii=False) + ";\n"
    EMBEDDED_JS_PATH.write_text(js_content, encoding="utf-8")


class ValidatorRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:
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

        if parsed.path == "/api/build":
            try:
                cmd = [sys.executable, str(ROOT_DIR / "tools" / "build_ptbr_rom.py")]
                p = subprocess.run(
                    cmd,
                    cwd=str(ROOT_DIR),
                    capture_output=True,
                    text=True,
                    encoding="utf-8"
                )
                if p.returncode == 0:
                    self._send_json({"ok": True, "output": p.stdout})
                else:
                    self._send_json({"ok": False, "error": p.stderr or p.stdout}, status=500)
            except Exception as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=500)
            return

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
    print(" VALIDADOR DE TRADUÇÃO GBA — SUMMON NIGHT: SWORDCRAFT STORY 2")
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
