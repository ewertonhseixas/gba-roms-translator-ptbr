# 🎨 GBA Pixel Studio — Editor Interativo de Imagens & Text-in-Tiles

Ferramenta visual de edição pixel art desenvolvida sob medida para a suíte de tradução e localização de ROMs de **Game Boy Advance (GBA)**.

---

## 🚀 Como Executar

Na raiz do repositório, execute:

```powershell
python -X utf8 "02_TRADUCAO_ROMS_GBA/_ferramentas_gerais/image_editor/image_editor_server.py"
```

No Windows, também é possível abrir `00_APPS_E_ATALHOS/editor_de_imagens.bat`.

O navegador padrão abrirá automaticamente em `http://127.0.0.1:8765/`.

---

## 🛠️ Recursos Principais

1. **Conformidade Estrita com Hardware GBA (PPU)**:
   - Preservação obrigatória de **Paleta Indexada** (4bpp / 16 cores e 8bpp / 256 cores).
   - **Índice 0 Protegido**: Sinalizado visualmente como transparência obrigatória de hardware.
   - Resolução e contagem de tiles 8x8 rigorosamente preservadas para não quebrar alinhamento de VRAM.

2. **Visualização e Auxílio Visual**:
   - **Grade de Tiles 8x8 do GBA (`T`)**: Desenha os limites dos blocos de 8x8 pixels com coordenadas e numeração de tiles.
   - **Grade de Pixels 1px (`G`)**: Linhas nítidas para visualização de cada pixel individual em zoom ampliado.
   - **Modo Fantasma / Guia Onion-Skin (`👻 Slider`)**: Mostra a imagem original em inglês/japonês como referência semi-transparente de fundo.
   - **Espiar Original Instantâneo (`Tab` ou `Espaço`)**: Segure a tecla para alternar e comparar a arte original com a versão editada.
   - **Prévia Real 1:1 (Mockup GBA)**: Veja a qualquer momento o resultado em escala 100% nativa de Game Boy Advance.

3. **Ferramentas de Desenho Pixel Art**:
   - ✏️ **Lápis (`B` / `P`)**: Desenho com espessura de 1px ou 2px.
   - 🧼 **Borracha (`E`)**: Pinta diretamente com o Índice 0 (Transparência).
   - 💧 **Conta-gotas (`I`)**: Clique para capturar o índice de qualquer pixel.
   - 🪣 **Balde de Tinta (`F` / `G`)**: Preenchimento contíguo de 4 direções.
   - 📏 **Linha Reta (`L`)**: Algoritmo de Bresenham com prévia em tempo real.
   - ⬜ **Retângulo (`R` / `U`)**: Contorno ou preenchido.
   - 🔲 **Seleção Retangular (`M`)**: Selecione e mova blocos de pixels livremente.
   - 🔤 **Carimbador de Texto (`T`)**: Digite o texto traduzido (ex: `NOVO JOGO`, `CARREGAR`, `ATACAR`, `CRÍTICO`) e carimbe com fontes pixel art pré-configuradas (com suporte a acentos PT-BR), refinando depois manualmente no lápis!

4. **Integração com o Pipeline de Tradução**:
   - Botão **Salvar no Projeto (`Ctrl + S`)**: Salva o PNG corrigido diretamente na pasta `fixes/graphics/` do jogo.
   - Criação automática de **backup (`.bak`)** ao sobrescrever.
   - Atualização automática do status da imagem na planilha `controle-de-imagens-com-texto.md` para `✅ Editado`.
   - Exportação direta de PNG para backup local.

---

## ⌨️ Tabela de Atalhos do Teclado

| Tecla / Atalho | Ação |
| :--- | :--- |
| `Ctrl + S` | **Salvar no Projeto** (grava em `fixes/` e atualiza Markdown) |
| `Ctrl + Z` / `Ctrl + Y` | Desfazer / Refazer histórico |
| `B` ou `P` | Lápis (Pencil) |
| `E` | Borracha (pinta índice 0 transparente) |
| `I` | Conta-gotas (Eyedropper) |
| `F` ou `G` | Balde de Tinta (Flood Fill) |
| `L` | Ferramenta Linha Reta |
| `R` / `U` | Retângulo (Contorno / Preenchido) |
| `M` | Seleção Retangular (Marquee) |
| `T` | Carimbador de Texto Pixel Art |
| `X` | Inverter Cor Primária / Secundária |
| `0` a `9` | Selecionar índice da paleta diretamente |
| `Tab` ou `Espaço` (segurar) | **Espiar Original da ROM** (comparação rápida) |
| `[` e `]` | Imagem Anterior / Próxima Imagem do Catálogo |
| `C` | Centralizar e Ajustar Tela |
| `Roda do Mouse` | Aumentar / Diminuir Zoom |
| `Botão do Meio` | Mover a tela (Pan) |
