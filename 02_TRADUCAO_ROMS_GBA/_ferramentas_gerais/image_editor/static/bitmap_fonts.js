/**
 * GBA Pixel Studio - Bitmap Fonts & Pixel Text Rasterizer
 * Suporte a fontes pixel art com caracteres acentuados PT-BR
 */

const BITMAP_FONTS = {
    // Fonte 5x7 clássica retro RPG
    "retro_5x7": {
        name: "5x7 Retro RPG",
        width: 5,
        height: 7,
        spacing: 1,
        // Matriz de glifos 5x7: cada string representa 1 linha de 5 pixels ('0' ou '1')
        glyphs: {
            'A': ["01110","10001","10001","11111","10001","10001","10001"],
            'B': ["11110","10001","10001","11110","10001","10001","11110"],
            'C': ["01111","10000","10000","10000","10000","10000","01111"],
            'D': ["11110","10001","10001","10001","10001","10001","11110"],
            'E': ["11111","10000","10000","11110","10000","10000","11111"],
            'F': ["11111","10000","10000","11110","10000","10000","10000"],
            'G': ["01111","10000","10000","10111","10001","10001","01111"],
            'H': ["10001","10001","10001","11111","10001","10001","10001"],
            'I': ["11111","00100","00100","00100","00100","00100","11111"],
            'J': ["00111","00010","00010","00010","00010","10010","01100"],
            'K': ["10001","10010","10100","11000","10100","10010","10001"],
            'L': ["10000","10000","10000","10000","10000","10000","11111"],
            'M': ["10001","11011","10101","10101","10001","10001","10001"],
            'N': ["10001","11001","10101","10011","10001","10001","10001"],
            'O': ["01110","10001","10001","10001","10001","10001","01110"],
            'P': ["11110","10001","10001","11110","10000","10000","10000"],
            'Q': ["01110","10001","10001","10001","10101","10010","01101"],
            'R': ["11110","10001","10001","11110","10100","10010","10001"],
            'S': ["01111","10000","10000","01110","00001","00001","11110"],
            'T': ["11111","00100","00100","00100","00100","00100","00100"],
            'U': ["10001","10001","10001","10001","10001","10001","01110"],
            'V': ["10001","10001","10001","10001","10001","01010","00100"],
            'W': ["10001","10001","10001","10101","10101","11011","10001"],
            'X': ["10001","10001","01010","00100","01010","10001","10001"],
            'Y': ["10001","10001","01010","00100","00100","00100","00100"],
            'Z': ["11111","00001","00010","00100","01000","10000","11111"],

            // Acentos PT-BR maiúsculos
            'Á': ["00100","01000","01110","10001","11111","10001","10001"],
            'À': ["01000","00100","01110","10001","11111","10001","10001"],
            'Â': ["00100","01010","01110","10001","11111","10001","10001"],
            'Ã': ["01010","10101","01110","10001","11111","10001","10001"],
            'É': ["00100","01000","11111","10000","11110","10000","11111"],
            'Ê': ["00100","01010","11111","10000","11110","10000","11111"],
            'Í': ["00100","01000","11111","00100","00100","00100","11111"],
            'Ó': ["00100","01000","01110","10001","10001","10001","01110"],
            'Ô': ["00100","01010","01110","10001","10001","10001","01110"],
            'Õ': ["01010","10101","01110","10001","10001","10001","01110"],
            'Ú': ["00100","01000","10001","10001","10001","10001","01110"],
            'Ç': ["01111","10000","10000","10000","01111","00100","01000"],

            // Minúsculas comuns
            'a': ["00000","00000","01110","00001","01111","10001","01111"],
            'c': ["00000","00000","01110","10000","10000","10000","01110"],
            'e': ["00000","00000","01110","10001","11111","10000","01110"],
            'i': ["00100","00000","01100","00100","00100","00100","01110"],
            'o': ["00000","00000","01110","10001","10001","10001","01110"],
            'r': ["00000","00000","10110","11001","10000","10000","10000"],
            's': ["00000","00000","01111","10000","01110","00001","11110"],
            't': ["00100","00100","11110","00100","00100","00101","00010"],
            'u': ["00000","00000","10001","10001","10001","10011","01101"],

            // Acentos minúsculos
            'á': ["00010","00100","01110","00001","01111","10001","01111"],
            'é': ["00010","00100","01110","10001","11111","10000","01110"],
            'í': ["00010","00100","01100","00100","00100","00100","01110"],
            'ó': ["00010","00100","01110","10001","10001","10001","01110"],
            'ú': ["00010","00100","10001","10001","10001","10011","01101"],
            'ç': ["00000","01110","10000","10000","01110","00100","01000"],

            // Números e pontuação
            '0': ["01110","10011","10101","11001","10001","10001","01110"],
            '1': ["00100","01100","00100","00100","00100","00100","01110"],
            '2': ["01110","10001","00001","00010","00100","01000","11111"],
            '3': ["11110","00001","00001","01110","00001","00001","11110"],
            '4': ["00010","00110","01010","10010","11111","00010","00010"],
            '5': ["11111","10000","11110","00001","00001","10001","01110"],
            '6': ["00110","01000","10000","11110","10001","10001","01110"],
            '7': ["11111","00001","00010","00100","00100","00100","00100"],
            '8': ["01110","10001","10001","01110","10001","10001","01110"],
            '9': ["01110","10001","10001","01111","00001","00010","01100"],
            ':': ["00000","00100","00000","00000","00100","00000","00000"],
            '!': ["00100","00100","00100","00100","00100","00000","00100"],
            '?': ["01110","10001","00001","00010","00100","00000","00100"],
            '/': ["00001","00010","00010","00100","01000","01000","10000"],
            '-': ["00000","00000","00000","11111","00000","00000","00000"],
            '.': ["00000","00000","00000","00000","00000","00110","00110"],
            ' ': ["00000","00000","00000","00000","00000","00000","00000"]
        }
    },

    // Fonte 4x6 mini para menus e labels pequenos
    "mini_4x6": {
        name: "4x6 Mini Compacta",
        width: 4,
        height: 6,
        spacing: 1,
        glyphs: {
            'A': ["0110","1001","1111","1001","1001","1001"],
            'B': ["1110","1001","1110","1001","1001","1110"],
            'C': ["0111","1000","1000","1000","1000","0111"],
            'D': ["1110","1001","1001","1001","1001","1110"],
            'E': ["1111","1000","1110","1000","1000","1111"],
            'F': ["1111","1000","1110","1000","1000","1000"],
            'G': ["0111","1000","1011","1001","1001","0111"],
            'H': ["1001","1001","1111","1001","1001","1001"],
            'I': ["111","010","010","010","010","111"],
            'L': ["1000","1000","1000","1000","1000","1111"],
            'M': ["1001","1111","1001","1001","1001","1001"],
            'N': ["1001","1101","1011","1001","1001","1001"],
            'O': ["0110","1001","1001","1001","1001","0110"],
            'P': ["1110","1001","1110","1000","1000","1000"],
            'R': ["1110","1001","1110","1010","1001","1001"],
            'S': ["0111","1000","0110","0001","1001","0110"],
            'T': ["1111","0100","0100","0100","0100","0100"],
            'U': ["1001","1001","1001","1001","1001","0110"],
            'V': ["1001","1001","1001","1001","0110","0100"],
            ' ': ["000","000","000","000","000","000"],
            '0': ["0110","1001","1001","1001","1001","0110"],
            '1': ["010","110","010","010","010","111"],
            '2': ["1110","0001","0110","1000","1000","1111"],
            '!': ["010","010","010","010","000","010"],
            ':': ["00","10","00","10","00","00"],
            '-': ["0000","0000","1111","0000","0000","0000"]
        }
    }
};

/**
 * Rasteriza texto em uma grade 2D de pixels
 * Retorna { width, height, grid: [[0/1/2,...]] }
 */
function renderPixelText(text, options = {}) {
    const fontKey = options.font || "retro_5x7";
    const mode = options.mode || "bitmap"; // "bitmap" ou "canvas"
    const textColor = options.textColorIndex ?? 1;
    const shadowColor = options.shadowColorIndex ?? 0;
    const addShadow = options.addShadow ?? false;
    const shadowType = options.shadowType || "drop"; // "drop" (1px down-right) ou "outline" (8-way)

    if (mode === "bitmap" && BITMAP_FONTS[fontKey]) {
        return renderWithBitmapFont(text, BITMAP_FONTS[fontKey], textColor, shadowColor, addShadow, shadowType);
    } else {
        return renderWithCanvas(text, options);
    }
}

function renderWithBitmapFont(text, font, textColor, shadowColor, addShadow, shadowType) {
    let totalW = 0;
    const chars = [];

    for (const ch of text) {
        // Tenta maiúscula se não achar
        let glyph = font.glyphs[ch] || font.glyphs[ch.toUpperCase()] || font.glyphs[' '];
        if (!glyph) glyph = font.glyphs[' '];
        const w = glyph[0].length;
        chars.push({ glyph, w });
        totalW += w + font.spacing;
    }
    if (chars.length > 0) {
        totalW -= font.spacing;
    }

    const padding = addShadow ? (shadowType === "outline" ? 2 : 1) : 0;
    const outW = totalW + (padding * 2);
    const outH = font.height + (padding * 2);

    // Grid inicializado com -1 (transparente / não desenhado)
    const grid = Array.from({ length: outH }, () => Array(outW).fill(-1));

    // Se tiver sombra/contorno, desenha primeiro
    if (addShadow && shadowColor >= 0) {
        const offsets = shadowType === "outline"
            ? [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, 1], [-1, 1], [1, -1]]
            : [[1, 1]];

        for (const [ox, oy] of offsets) {
            let curX = padding + ox;
            for (const { glyph, w } of chars) {
                for (let y = 0; y < glyph.length; y++) {
                    for (let x = 0; x < w; x++) {
                        if (glyph[y][x] === '1') {
                            const px = curX + x;
                            const py = padding + oy + y;
                            if (px >= 0 && px < outW && py >= 0 && py < outH) {
                                grid[py][px] = shadowColor;
                            }
                        }
                    }
                }
                curX += w + font.spacing;
            }
        }
    }

    // Desenha as letras na cor primária
    let curX = padding;
    for (const { glyph, w } of chars) {
        for (let y = 0; y < glyph.length; y++) {
            for (let x = 0; x < w; x++) {
                if (glyph[y][x] === '1') {
                    const px = curX + x;
                    const py = padding + y;
                    if (px >= 0 && px < outW && py >= 0 && py < outH) {
                        grid[py][px] = textColor;
                    }
                }
            }
        }
        curX += w + font.spacing;
    }

    return { width: outW, height: outH, grid };
}

function renderWithCanvas(text, options) {
    const fontSize = options.fontSize || 10;
    const fontFamily = options.fontFamily || "monospace";
    const fontWeight = options.bold ? "bold" : "normal";
    const textColor = options.textColorIndex ?? 1;
    const shadowColor = options.shadowColorIndex ?? 0;
    const addShadow = options.addShadow ?? false;
    const shadowType = options.shadowType || "drop";

    const offscreen = document.createElement("canvas");
    const ctx = offscreen.getContext("2d", { willReadFrequently: true });
    ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
    ctx.textBaseline = "top";

    const metrics = ctx.measureText(text);
    const textW = Math.ceil(metrics.width) + 2;
    const textH = Math.ceil(fontSize * 1.2) + 2;

    offscreen.width = textW;
    offscreen.height = textH;

    // Fundo limpo
    ctx.clearRect(0, 0, textW, textH);
    ctx.font = `${fontWeight} ${fontSize}px ${fontFamily}`;
    ctx.textBaseline = "top";
    ctx.fillStyle = "#ffffff";
    ctx.imageSmoothingEnabled = false;
    ctx.fillText(text, 1, 1);

    const imgData = ctx.getImageData(0, 0, textW, textH);
    const data = imgData.data;

    // Encontra caixa delimitadora (crop)
    let minX = textW, maxX = 0, minY = textH, maxY = 0;
    for (let y = 0; y < textH; y++) {
        for (let x = 0; x < textW; x++) {
            const alpha = data[(y * textW + x) * 4 + 3];
            if (alpha > 120) {
                if (x < minX) minX = x;
                if (x > maxX) maxX = x;
                if (y < minY) minY = y;
                if (y > maxY) maxY = y;
            }
        }
    }

    if (minX > maxX) {
        // Texto vazio
        return { width: 1, height: 1, grid: [[-1]] };
    }

    const cropW = maxX - minX + 1;
    const cropH = maxY - minY + 1;
    const padding = addShadow ? (shadowType === "outline" ? 2 : 1) : 0;
    const outW = cropW + (padding * 2);
    const outH = cropH + (padding * 2);

    const grid = Array.from({ length: outH }, () => Array(outW).fill(-1));

    // Sombra se solicitada
    if (addShadow && shadowColor >= 0) {
        const offsets = shadowType === "outline"
            ? [[-1, 0], [1, 0], [0, -1], [0, 1], [-1, -1], [1, 1], [-1, 1], [1, -1]]
            : [[1, 1]];

        for (const [ox, oy] of offsets) {
            for (let y = 0; y < cropH; y++) {
                for (let x = 0; x < cropW; x++) {
                    const srcX = minX + x;
                    const srcY = minY + y;
                    const alpha = data[(srcY * textW + srcX) * 4 + 3];
                    if (alpha > 120) {
                        const px = padding + ox + x;
                        const py = padding + oy + y;
                        if (px >= 0 && px < outW && py >= 0 && py < outH) {
                            grid[py][px] = shadowColor;
                        }
                    }
                }
            }
        }
    }

    // Desenha letras primárias
    for (let y = 0; y < cropH; y++) {
        for (let x = 0; x < cropW; x++) {
            const srcX = minX + x;
            const srcY = minY + y;
            const alpha = data[(srcY * textW + srcX) * 4 + 3];
            if (alpha > 120) {
                const px = padding + x;
                const py = padding + y;
                if (px >= 0 && px < outW && py >= 0 && py < outH) {
                    grid[py][px] = textColor;
                }
            }
        }
    }

    return { width: outW, height: outH, grid };
}
