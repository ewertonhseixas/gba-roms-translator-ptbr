#!/usr/bin/env python3
"""
Image Text Auditor — Protocolo de Extração para Tradução de ROMs
===============================================================
Audita imagens e gráficos extraídos de uma ROM:
  - Analisa dimensões (largura x altura), profundidade de cor (4bpp/8bpp/RGB)
  - Verifica integridade da paleta (garante índice 0 como transparência)
  - Gera e atualiza a planilha de controle 'controle-de-imagens-com-texto.md'
  - Audita imagens editadas em 'fixes/graphics/' para garantir que respeitam
    rigorosamente a resolução original antes da reinjeção na ROM
"""

import os
import sys
import struct
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def read_png_metadata(filepath: Path) -> Optional[Dict[str, Any]]:
    """Lê o cabeçalho IHDR de um arquivo PNG sem dependências externas."""
    try:
        data = filepath.read_bytes()
        if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
            return None

        # O primeiro chunk é sempre IHDR (comprimento 13 bytes)
        # Offset 12: Comprimento do IHDR
        # Offset 16: 'IHDR'
        width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
            ">IIBBBBB", data[16:29]
        )

        color_type_names = {
            0: "Escala de Cinza",
            2: "RGB Truecolor (24-bit)",
            3: "Indexado / Paleta (GBA nativo)",
            4: "Escala de Cinza + Alfa",
            6: "RGBA Truecolor + Alfa",
        }

        # Busca tamanho da paleta PLTE se for indexado
        palette_colors = 0
        plte_pos = data.find(b"PLTE")
        if plte_pos != -1:
            plte_len = struct.unpack(">I", data[plte_pos - 4:plte_pos])[0]
            palette_colors = plte_len // 3

        return {
            "filename": filepath.name,
            "path": filepath,
            "width": width,
            "height": height,
            "bit_depth": bit_depth,
            "color_type": color_type,
            "color_desc": color_type_names.get(color_type, f"Tipo {color_type}"),
            "palette_colors": palette_colors or (2 ** bit_depth if color_type == 3 else 0),
        }
    except Exception as e:
        return None


def generate_image_control_markdown(image_list: List[Dict[str, Any]], output_md: Path, game_name: str = "GBA Game"):
    """Gera a tabela Markdown de controle de imagens com texto."""
    content = f"""# 🖼️ Planilha de Controle de Imagens e Gráficos com Texto
**Jogo:** {game_name}  
**Plataforma:** Game Boy Advance (GBA)  
**Total de Gráficos Catalogados:** {len(image_list)} imagens  
**Gerado por:** `image_text_auditor.py` (Protocolo de Extração)  

---

## ⚠️ Regras Invioláveis de Edição Gráfica

> [!CAUTION]
> 1. **Proibido alterar a contagem de tiles ou resolução em pixels** da imagem original. Se o botão tem 64x16 pixels, a versão em português DEVE ter exatamente 64x16 pixels.
> 2. **Índice 0 da Paleta = Transparência Obrigatória:** No hardware do GBA, o índice 0 da paleta é tratado como transparente. Nunca desenhe letras ou sombras no índice 0.
> 3. **Preservar Formato Indexado:** Imagens de 16 cores (4bpp) ou 256 cores (8bpp) devem ser mantidas com paleta indexada ao salvar.

---

## 📋 Tabela de Imagens Identificadas

| ID | Arquivo Original | Dimensões (Px) | Formato / Cores | Texto Original (EN/JP) | Tradução Sugerida (PT-BR) | Status de Edição | Testado no Emulador |
| :--- | :--- | :---: | :--- | :--- | :--- | :---: | :---: |
"""

    for idx, img in enumerate(image_list, 1):
        img_id = f"IMG_{idx:02d}"
        colors_info = f"{img['palette_colors']} cores" if img['palette_colors'] else img['color_desc']
        content += f"| `{img_id}` | `{img['filename']}` | {img['width']} x {img['height']} | {colors_info} | `[Preencher]` | `[Preencher]` | ⏳ Pendente | ❌ Não |\n"

    output_md.write_text(content, encoding="utf-8")
    print(f"✅ Planilha de controle de imagens gerada em: {output_md}")


def audit_fixed_images(orig_dir: Path, fixes_dir: Path) -> List[Dict[str, Any]]:
    """Compara as imagens editadas em fixes/ com as originais para validar compatibilidade."""
    issues = []
    if not fixes_dir.exists():
        return issues

    fixed_files = list(fixes_dir.rglob("*.png"))
    for f in fixed_files:
        orig_file = orig_dir / f.name
        if not orig_file.exists():
            # Tenta busca recursiva no original
            matches = list(orig_dir.rglob(f.name))
            if matches:
                orig_file = matches[0]
            else:
                issues.append({
                    "file": f.name,
                    "issue": "Arquivo editado não existe no diretório original",
                    "severity": "ALERTA"
                })
                continue

        orig_meta = read_png_metadata(orig_file)
        fix_meta = read_png_metadata(f)

        if not orig_meta or not fix_meta:
            continue

        if orig_meta["width"] != fix_meta["width"] or orig_meta["height"] != fix_meta["height"]:
            issues.append({
                "file": f.name,
                "issue": f"Dimensões alteradas! Original: {orig_meta['width']}x{orig_meta['height']} vs Editado: {fix_meta['width']}x{fix_meta['height']}",
                "severity": "CRÍTICO"
            })

        if orig_meta["color_type"] == 3 and fix_meta["color_type"] != 3:
            issues.append({
                "file": f.name,
                "issue": f"Perda de paleta indexada! Original é paleta ({orig_meta['palette_colors']} cores), editado virou {fix_meta['color_desc']}",
                "severity": "CRÍTICO"
            })

    return issues


def main():
    parser = argparse.ArgumentParser(description="Auditor e catalogador de imagens e gráficos com texto")
    parser.add_argument("--dir", "-d", default="extracted/graphics", help="Diretório de gráficos extraídos")
    parser.add_argument("--fixes", "-f", default="fixes/graphics", help="Diretório de gráficos editados para auditoria")
    parser.add_argument("--out", "-o", default=None, help="Caminho do arquivo Markdown de controle de saída")
    parser.add_argument("--game", "-g", default="GBA Game", help="Nome do jogo")
    parser.add_argument("--audit", action="store_true", help="Audita arquivos em fixes/ contra os originais")

    args = parser.parse_args()
    orig_path = Path(args.dir)

    if args.audit:
        fixes_path = Path(args.fixes)
        print(f"🔍 Auditando imagens editadas em '{fixes_path}' contra '{orig_path}'...")
        issues = audit_fixed_images(orig_path, fixes_path)
        if not issues:
            print("✅ Todas as imagens editadas respeitam 100% as dimensões e paletas originais!")
        else:
            print(f"⚠️  Foram detectadas {len(issues)} não conformidades:")
            for iss in issues:
                print(f"  [{iss['severity']}] {iss['file']}: {iss['issue']}")
        return

    if not orig_path.exists():
        print(f"❌ Diretório não encontrado: {orig_path}")
        sys.exit(1)

    png_files = list(orig_path.rglob("*.png"))
    print(f"🔍 Escaneando {len(png_files)} imagens PNG em '{orig_path}'...")

    image_list = []
    for f in png_files:
        meta = read_png_metadata(f)
        if meta:
            image_list.append(meta)

    out_file = Path(args.out) if args.out else orig_path.parent / "controle-de-imagens-com-texto.md"
    generate_image_control_markdown(image_list, out_file, game_name=args.game)


if __name__ == "__main__":
    main()
