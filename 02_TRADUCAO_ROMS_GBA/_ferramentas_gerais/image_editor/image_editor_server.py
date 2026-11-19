#!/usr/bin/env python3
"""
GBA Pixel Studio & Image Text Editor (Server Backend)
====================================================
Servidor local HTTP para edição pixel art e injeção de imagens com texto
para traduções de ROMs de Game Boy Advance (Summon Night 1, 2 e outros).

- Carrega imagens extraídas da ROM e versões corrigidas (fixes/)
- Preserva estritamente a paleta indexada (4bpp / 16 cores ou 8bpp / 256 cores)
- Mantém o Índice 0 como transparência inviolável de hardware (PPU do GBA)
- Atualiza automaticamente a planilha 'controle-de-imagens-com-texto.md'
- Zero dependências pesadas: apenas Python padrão e Pillow (PIL)
"""

import os
import sys
import json
import shutil
import socket
import urllib.parse
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

# Configuração de encoding UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Diretórios base do projeto
SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = SCRIPT_DIR.parent.parent
STATIC_DIR = SCRIPT_DIR / "static"

GAMES_CONFIG = {
    "sn1": {
        "id": "sn1",
        "name": "Summon Night: Swordcraft Story 1 (GBA)",
        "base_dir": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_1",
        "control_md": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_1" / "ARQUIVOS md" / "controle-de-imagens-com-texto.md",
        "extracted_dir": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_1" / "extracted" / "graphics",
        "fixes_dir": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_1" / "fixes" / "graphics",
    },
    "sn2": {
        "id": "sn2",
        "name": "Summon Night: Swordcraft Story 2 (GBA)",
        "base_dir": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_2",
        "control_md": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_2" / "ARQUIVOS md" / "controle-de-imagens-com-texto.md",
        "extracted_dir": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_2" / "extracted" / "graphics",
        "fixes_dir": WORKSPACE_DIR / "02_TRADUCAO_ROMS_GBA" / "jogos" / "Summon_Night_Swordcraft_Story_2" / "fixes" / "graphics",
    },
    "port": {
        "id": "port",
        "name": "Port PC / Android",
        "base_dir": WORKSPACE_DIR / "01_PORT_PC_ANDROID",
        "control_md": None,
        "extracted_dir": WORKSPACE_DIR / "01_PORT_PC_ANDROID" / "extracted" / "graphics",
        "fixes_dir": WORKSPACE_DIR / "01_PORT_PC_ANDROID" / "fixes" / "graphics",
    }
}


def parse_control_markdown(md_path: Path) -> List[Dict[str, Any]]:
    """Lê e analisa a tabela de controle de imagens com texto."""
    if not md_path or not md_path.exists():
        return []

    items = []
    lines = md_path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        line_s = line.strip()
        if line_s.startswith("|") and "IMG_" in line_s:
            parts = [p.strip() for p in line_s.split("|")[1:-1]]
            if len(parts) >= 7:
                is_short = (len(parts) == 7)
                img_id = parts[0].strip("`").strip()
                if is_short:
                    loc = parts[1].strip("`").strip()
                    filename = loc
                    dims = parts[2].strip("`").strip()
                    fmt = parts[3].strip("`").strip()
                    orig_text = parts[4].replace("<br>", " ").strip("`").strip()
                    sugg_text = parts[5].replace("<br>", " ").strip("`").strip()
                    status = parts[6].strip()
                    tested = ""
                else:
                    filename = parts[1].strip("`").strip()
                    loc = parts[2].strip("`").strip()
                    dims = parts[3].strip("`").strip()
                    fmt = parts[4].strip("`").strip()
                    orig_text = parts[5].replace("<br>", " ").strip("`").strip()
                    sugg_text = parts[6].replace("<br>", " ").strip("`").strip()
                    status = parts[7].strip()
                    tested = parts[8].strip() if len(parts) > 8 else ""

                # Extrai largura x altura
                width, height = 0, 0
                if "x" in dims.lower():
                    dim_parts = dims.lower().split("x")
                    try:
                        width = int(dim_parts[0].strip())
                        height = int(dim_parts[1].strip())
                    except ValueError:
                        pass

                items.append({
                    "id": img_id,
                    "filename": filename,
                    "location": loc,
                    "dims": dims,
                    "width": width,
                    "height": height,
                    "format": fmt,
                    "orig_text": orig_text,
                    "sugg_text": sugg_text,
                    "status": status,
                    "tested": tested,
                })
    return items


def find_image_file(base_dir: Path, rel_path: str) -> Optional[Path]:
    """Tenta localizar um arquivo de imagem por caminho relativo ou busca recursiva."""
    if not base_dir or not base_dir.exists():
        return None

    norm = Path(rel_path.replace("\\", "/"))
    # 1. Caminho direto relativo
    p1 = base_dir / norm
    if p1.exists() and p1.is_file():
        return p1

    # 2. Tenta dentro de telas_e_menus
    p2 = base_dir / "telas_e_menus" / norm.name
    if p2.exists() and p2.is_file():
        return p2

    # 3. Busca recursiva pelo nome do arquivo
    matches = list(base_dir.rglob(norm.name))
    if matches and matches[0].is_file():
        return matches[0]

    return None


def read_image_pixels_and_palette(path: Path) -> Dict[str, Any]:
    """Lê imagem usando Pillow e extrai paleta indexada e matriz de pixels 1D."""
    im = Image.open(path)
    w, h = im.size
    is_indexed = (im.mode == "P")
    palette = []

    if is_indexed:
        raw_pal = im.getpalette() or []
        # Cria lista de cores RGB [[r, g, b], ...]
        for i in range(0, min(len(raw_pal), 768), 3):
            palette.append([raw_pal[i], raw_pal[i + 1], raw_pal[i + 2]])
        # Pixels como índices da paleta (0 a 15 ou 0 a 255)
        raw_data = list(im.get_flattened_data() if hasattr(im, "get_flattened_data") else im.getdata())
        pixels = [int(p) for p in raw_data]
    else:
        # Se for RGBA ou RGB, constrói paleta com índice 0 transparente
        im_rgba = im.convert("RGBA")
        raw_items = list(im_rgba.get_flattened_data() if hasattr(im_rgba, "get_flattened_data") else im_rgba.getdata())
        palette = [[0, 0, 0]]  # Índice 0 = transparente
        color_map = {}
        pixels = []

        for item in raw_items:
            # item é uma tupla (r, g, b, a)
            if isinstance(item, (tuple, list)):
                r, g, b = int(item[0]), int(item[1]), int(item[2])
                a = int(item[3]) if len(item) > 3 else 255
            else:
                r, g, b, a = 0, 0, 0, 0

            if a < 128:
                pixels.append(0)
            else:
                rgb = (r, g, b)
                if rgb not in color_map:
                    if len(palette) >= 256:
                        # Mapeia para a cor mais próxima se exceder limite de 256 cores do hardware
                        color_map[rgb] = min(
                            range(1, len(palette)),
                            key=lambda idx: (palette[idx][0] - r) ** 2 + (palette[idx][1] - g) ** 2 + (palette[idx][2] - b) ** 2
                        )
                    else:
                        color_map[rgb] = len(palette)
                        palette.append([r, g, b])
                pixels.append(color_map[rgb])

    # Preenche paleta mínima de 16 cores se for 4bpp
    if len(palette) < 16:
        while len(palette) < 16:
            palette.append([0, 0, 0])

    return {
        "width": w,
        "height": h,
        "mode": im.mode,
        "is_indexed": is_indexed,
        "palette": palette,
        "pixels": pixels,
    }


def update_markdown_status(md_path: Path, item_id: str, new_status: str = "✅ Editado") -> bool:
    """Atualiza a coluna de status de uma imagem na tabela do Markdown."""
    if not md_path or not md_path.exists():
        return False

    lines = md_path.read_text(encoding="utf-8").splitlines()
    modified = False
    new_lines = []
    clean_id = item_id.strip("`").strip()

    for line in lines:
        if f"`{clean_id}`" in line or f"| {clean_id} " in line:
            parts = line.split("|")
            if len(parts) >= 8:
                # SN1 usa 9 colunas (índice 8), SN2 usa 7 colunas (índice 7)
                status_idx = 8 if len(parts) >= 10 else 7
                parts[status_idx] = f" {new_status} "
                line = "|".join(parts)
                modified = True
        new_lines.append(line)

    if modified:
        md_path.write_text("\n".join(new_lines), encoding="utf-8")
    return modified


class GBAImageEditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            params = urllib.parse.parse_qs(parsed.query)

            if path == "/api/games":
                self.send_json([
                    {"id": "sn1", "name": "Summon Night 1: Swordcraft Story (GBA)", "has_catalog": True},
                    {"id": "sn2", "name": "Summon Night 2: Swordcraft Story 2 (GBA)", "has_catalog": True},
                    {"id": "port", "name": "Port PC / Android", "has_catalog": False},
                ])
                return

            if path == "/api/catalog":
                game_id = params.get("game", ["sn1"])[0]
                cfg = GAMES_CONFIG.get(game_id, GAMES_CONFIG["sn1"])
                items = parse_control_markdown(cfg["control_md"])

                # Anota caminhos reais de cada item
                for item in items:
                    orig_file = find_image_file(cfg["extracted_dir"], item["filename"])
                    item["original_found"] = orig_file is not None
                    item["original_path"] = str(orig_file.relative_to(WORKSPACE_DIR)) if orig_file else ""

                    # Verifica se já existe um fix salvo
                    if orig_file and cfg["fixes_dir"].exists():
                        try:
                            rel = orig_file.relative_to(cfg["extracted_dir"])
                            fix_file = cfg["fixes_dir"] / rel
                            item["fix_found"] = fix_file.exists()
                            item["fix_path"] = str(fix_file.relative_to(WORKSPACE_DIR)) if fix_file.exists() else ""
                        except Exception:
                            item["fix_found"] = False
                            item["fix_path"] = ""
                    else:
                        item["fix_found"] = False
                        item["fix_path"] = ""

                self.send_json({"game": game_id, "name": cfg["name"], "items": items})
                return

            if path == "/api/image_data":
                game_id = params.get("game", ["sn1"])[0]
                rel_path = params.get("path", [""])[0]
                img_id = params.get("id", [""])[0]
                cfg = GAMES_CONFIG.get(game_id, GAMES_CONFIG["sn1"])

                # Localiza o arquivo original
                orig_file = find_image_file(cfg["extracted_dir"], rel_path)
                if not orig_file and img_id:
                    # Tenta buscar pelo catálogo
                    items = parse_control_markdown(cfg["control_md"])
                    for it in items:
                        if it["id"] == img_id:
                            orig_file = find_image_file(cfg["extracted_dir"], it["filename"])
                            break

                if not orig_file:
                    self.send_json({"error": f"Arquivo original '{rel_path}' não encontrado."}, status=404)
                    return

                # Verifica se já existe um fix salvo
                rel_to_extracted = orig_file.relative_to(cfg["extracted_dir"])
                fix_file = cfg["fixes_dir"] / rel_to_extracted
                has_fix = fix_file.exists()

                # Lê dados da imagem original (para referência / onion-skin)
                orig_data = read_image_pixels_and_palette(orig_file)

                # Se já existir fix, carrega ele no canvas; senão, carrega o original
                if has_fix:
                    edit_data = read_image_pixels_and_palette(fix_file)
                else:
                    edit_data = orig_data

                response = {
                    "id": img_id,
                    "game": game_id,
                    "rel_path": str(rel_to_extracted).replace("\\", "/"),
                    "filename": orig_file.name,
                    "width": orig_data["width"],
                    "height": orig_data["height"],
                    "palette": edit_data["palette"],
                    "pixels": edit_data["pixels"],
                    "orig_palette": orig_data["palette"],
                    "orig_pixels": orig_data["pixels"],
                    "has_fix": has_fix,
                    "fix_file_exists": has_fix,
                    "target_rel_fix": str(fix_file.relative_to(WORKSPACE_DIR)).replace("\\", "/"),
                }
                self.send_json(response)
                return

            if path == "/api/search_extracted":
                game_id = params.get("game", ["sn1"])[0]
                query = params.get("q", [""])[0].lower()
                cfg = GAMES_CONFIG.get(game_id, GAMES_CONFIG["sn1"])

                results = []
                if cfg["extracted_dir"] and cfg["extracted_dir"].exists():
                    for p in cfg["extracted_dir"].rglob("*.png"):
                        rel = str(p.relative_to(cfg["extracted_dir"])).replace("\\", "/")
                        if not query or query in rel.lower():
                            results.append({
                                "name": p.name,
                                "rel_path": rel,
                            })
                            if len(results) >= 200:
                                break

                self.send_json({"results": results, "total": len(results)})
                return

            # Servir arquivo estático normal
            super().do_GET()
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": f"Erro interno do servidor: {str(e)}"}, status=500)

    def do_POST(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path == "/api/save_image":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)

                game_id = data.get("game", "sn1")
                rel_path = data.get("rel_path", "")
                img_id = data.get("id", "")
                width = int(data.get("width", 0))
                height = int(data.get("height", 0))
                palette = data.get("palette", [])
                pixels = data.get("pixels", [])
                mark_completed = data.get("mark_completed", True)

                cfg = GAMES_CONFIG.get(game_id, GAMES_CONFIG["sn1"])

                if not rel_path or width <= 0 or height <= 0 or len(pixels) != (width * height):
                    self.send_json({
                        "error": f"Dados inválidos: pixels={len(pixels)}, esperava={width*height}."
                    }, status=400)
                    return

                target_file = cfg["fixes_dir"] / Path(rel_path.replace("\\", "/"))
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # Cria backup (.bak) se já existia versão anterior
                backup_created = False
                if target_file.exists():
                    bak_path = target_file.with_suffix(".png.bak")
                    shutil.copy2(target_file, bak_path)
                    backup_created = True

                # Constrói a imagem indexada (P) com estrito respeito à paleta do GBA
                flat_palette = []
                for col in palette:
                    flat_palette.extend([int(col[0]), int(col[1]), int(col[2])])
                # Preenche até 768 itens (256 cores x 3 canais)
                while len(flat_palette) < 768:
                    flat_palette.extend([0, 0, 0])

                out_im = Image.new("P", (width, height))
                out_im.putpalette(flat_palette)
                out_im.putdata([int(p) for p in pixels])

                # Salva PNG indexado com transparência no índice 0 (padrão GBA)
                out_im.save(target_file, format="PNG", transparency=0)

                # Atualiza o status na planilha Markdown
                md_updated = False
                if mark_completed and cfg["control_md"] and img_id:
                    md_updated = update_markdown_status(cfg["control_md"], img_id, "✅ Editado")

                self.send_json({
                    "success": True,
                    "saved_path": str(target_file.relative_to(WORKSPACE_DIR)).replace("\\", "/"),
                    "bytes": target_file.stat().st_size,
                    "backup_created": backup_created,
                    "md_updated": md_updated,
                })
                return

            self.send_json({"error": "Endpoint não encontrado"}, status=404)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json({"error": f"Erro interno do servidor: {str(e)}"}, status=500)

    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def find_free_port(start_port: int = 8765, max_attempts: int = 20) -> int:
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def main():
    port = find_free_port(8765)
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, GBAImageEditorHandler)

    url = f"http://127.0.0.1:{port}/"
    print("=" * 65)
    print("  🎨 GBA Pixel Studio & Image Text Editor (Tradução GBA)")
    print("=" * 65)
    print(f"  Servidor iniciado em: {url}")
    print("  Pressione Ctrl+C na janela para encerrar o servidor.")
    print("=" * 65)

    # Abre o navegador automaticamente
    webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        httpd.server_close()
        print("Servidor finalizado com sucesso.")


if __name__ == "__main__":
    main()
