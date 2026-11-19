#!/usr/bin/env python3
"""
Edita os PNGs paletizados (mode='P') em extracted/graphics_ui/ traduzindo os textos
para PT-BR, preservando 100% a paleta original e o índice 0 de transparência.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def draw_pixel_text(
    img: Image.Image,
    box: tuple[int, int, int, int],
    lines: list[str],
    fill_idx: int,
    outline_idx: int | None,
    bg_idx: int,
):
    """Limpa a região `box` com `bg_idx` e desenha `lines` em pixel-art sem anti-aliasing."""
    x0, y0, x1, y1 = box
    pixels = img.load()
    for y in range(y0, min(y1, img.height)):
        for x in range(x0, min(x1, img.width)):
            pixels[x, y] = bg_idx

    # Renderiza texto em imagem 1-bit para evitar qualquer anti-aliasing
    w, h = x1 - x0, y1 - y0
    mask = Image.new("1", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    font = ImageFont.load_default()

    cy = 2
    for line in lines:
        draw.text((2, cy), line, fill=1, font=font)
        cy += 11

    m_pix = mask.load()
    # Contorno opcional (4-vizinhos)
    if outline_idx is not None:
        for y in range(h):
            for x in range(w):
                if m_pix[x, y]:
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not m_pix[nx, ny]:
                            pixels[x0 + nx, y0 + ny] = outline_idx

    # Preenchimento
    for y in range(h):
        for x in range(w):
            if m_pix[x, y]:
                pixels[x0 + x, y0 + y] = fill_idx


def main():
    png_dir = Path("03_TRADUCAO_ROMS_NDS/jogos/Summon Night (Japan)/extracted/graphics_ui")

    # 1. sn0_cs_sub_title.png (128x80)
    p = png_dir / "charaselect__sn0_cs_sub_title.png"
    img = Image.open(p)
    draw_pixel_text(img, (0, 0, 128, 40), ["Escolha o", "Protagonista"], fill_idx=1, outline_idx=2, bg_idx=0)
    draw_pixel_text(img, (0, 40, 128, 80), ["Seleção de", "Personagem"], fill_idx=1, outline_idx=2, bg_idx=0)
    img.save(p)
    print(f"[PATCH] {p.name}")

    # 2. sn0_cs_main_bot.png (128x72)
    p = png_dir / "charaselect__sn0_cs_main_bot.png"
    img = Image.open(p)
    draw_pixel_text(img, (0, 40, 64, 56), ["Voltar"], fill_idx=1, outline_idx=2, bg_idx=0)
    draw_pixel_text(img, (64, 40, 128, 56), ["Confirmar"], fill_idx=1, outline_idx=2, bg_idx=0)
    img.save(p)
    print(f"[PATCH] {p.name}")

    # 3. sn0_cs_sub_pane00..03.png (128x112)
    descs = {
        "charaselect__sn0_cs_sub_pane00.png": [
            "Jovem de coração",
            "forte que encara",
            "qualquer desafio",
            "de frente.",
        ],
        "charaselect__sn0_cs_sub_pane01.png": [
            "Garota determinada",
            "que nunca desiste",
            "diante das",
            "dificuldades.",
        ],
        "charaselect__sn0_cs_sub_pane02.png": [
            "Rapaz gentil e",
            "atento, sempre",
            "pronto para ajudar",
            "os amigos.",
        ],
        "charaselect__sn0_cs_sub_pane03.png": [
            "Jovem alegre e",
            "curiosa, cheia de",
            "energia para",
            "explorar.",
        ],
    }
    for fname, lines in descs.items():
        p = png_dir / fname
        img = Image.open(p)
        # Descobre a cor de fundo predominante (não-zero) do painel
        hist = img.histogram()[:16]
        bg_idx = max(range(1, 16), key=lambda i: hist[i])
        draw_pixel_text(img, (4, 8, 124, 96), lines, fill_idx=1, outline_idx=2, bg_idx=bg_idx)
        img.save(p)
        print(f"[PATCH] {p.name}")

    # 4. input__input_sp_main0000.png (128x168)
    p = png_dir / "input__input_sp_main0000.png"
    img = Image.open(p)
    draw_pixel_text(img, (0, 64, 64, 80), ["Aleatório"], fill_idx=1, outline_idx=2, bg_idx=0)
    draw_pixel_text(img, (64, 64, 128, 80), ["Apagar"], fill_idx=1, outline_idx=2, bg_idx=0)
    draw_pixel_text(img, (0, 80, 64, 96), ["Confirmar"], fill_idx=1, outline_idx=2, bg_idx=0)
    draw_pixel_text(img, (64, 80, 128, 96), ["Voltar"], fill_idx=1, outline_idx=2, bg_idx=0)
    img.save(p)
    print(f"[PATCH] {p.name}")


if __name__ == "__main__":
    main()
