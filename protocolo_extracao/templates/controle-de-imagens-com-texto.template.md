# 🖼️ Planilha de Controle de Imagens e Gráficos com Texto
**Jogo:** [NOME DO JOGO]  
**Plataforma:** GBA / [CONSOLA]  
**Status Geral:** Em Auditoria  

Este documento registra **todas as imagens extraídas da ROM que contêm textos embutidos** (Title Screen, Game Over, botões de menus, gráficos de mapas, tutoriais ilustrados). Serve para controlar o ciclo de edição gráfica, garantindo que o texto traduzido respeite as dimensões em pixels, limitações de paleta e alocação de VRAM.

---

## ⚠️ Regras Invioláveis de Edição Gráfica

> [!CAUTION]
> 1. **Proibido alterar a contagem de tiles ou resolução em pixels** da imagem original. Exemplo: Se o botão original tem 64x16 pixels (8x2 tiles), o botão em português DEVE ter exatamente 64x16 pixels.
> 2. **Índice de Cor 0 = Transparência Obrigatória:** No hardware de GBA, a primeira cor da paleta (índice 0) é SEMPRE interpretada pelo chip de vídeo como transparente. Nunca desenhe pixels de texto ou sombreamento usando a cor do índice 0.
> 3. **Profundidade de Cor:** Imagens 4bpp (16 cores) e 8bpp (256 cores) devem ser reimportadas como PNG indexado com a mesma paleta original.

---

## 📋 Tabela de Controle de Imagens com Texto

| ID | Nome do Arquivo PNG | Offset ROM / Arquivo | Dimensões (Px) | Formato / Cores | Texto Original (EN/JP) | Texto Traduzido (PT-BR) | Status de Edição | Testado no Emulador |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| `IMG_01` | `title_logo_sub.png` | `0x085C0100` | 128 x 32 | 4bpp / 16 cores | `Swordcraft Story` | `A História da Forja` | ⏳ Pendente | ❌ Não |
| `IMG_02` | `menu_btn_equip.png` | `0x085C1480` | 64 x 16 | 4bpp / 16 cores | `EQUIP` | `EQUIPAR` | ⏳ Pendente | ❌ Não |
| `IMG_03` | `menu_btn_item.png` | `0x085C1500` | 64 x 16 | 4bpp / 16 cores | `ITEM` | `ITENS` | ⏳ Pendente | ❌ Não |
| `IMG_04` | `menu_btn_status.png`| `0x085C1580` | 64 x 16 | 4bpp / 16 cores | `STATUS` | `STATUS` | ⏳ Pendente | ❌ Não |
| `IMG_05` | `game_over.png` | `0x085E2000` | 240 x 160 | 8bpp / 256 cores | `GAME OVER` | `FIM DE JOGO` | ⏳ Pendente | ❌ Não |
| `IMG_06` | `map_label_tower.png`| `0x08603200` | 96 x 24 | 4bpp / 16 cores | `Central Tower` | `Torre Central` | ⏳ Pendente | ❌ Não |

---

## 🛠️ Procedimento Operacional Padrão (SOP de Imagens)

1. **Extração Inicial:**
   - Execute o script extrator gráfico do jogo (`extract_all_graphics.py`).
   - Os arquivos são salvos na pasta `extracted/graphics/`.
2. **Triagem Visual:**
   - Um script de auditoria ou inspeção visual filtra quais PNGs possuem caracteres alfabéticos desenhados.
   - Cada imagem com texto recebe um ID sequencial (`IMG_01`, `IMG_02`...) nesta planilha.
3. **Edição Pixel Art:**
   - Abra a imagem original em um editor que suporte paleta indexada (Aseprite, Photoshop, GIMP ou GraphicsGale).
   - Redesenhe o texto em português mantendo a estética, tipografia e sombreamento pixel art do original.
   - Salve a imagem editada na pasta `fixes/graphics/` com o mesmo nome e resolução.
4. **Reinjeção e Teste:**
   - Execute o script injetor de gráficos para inserir os novos tiles na ROM traduzida.
   - Abra a ROM no mGBA e navegue até a tela do jogo onde a imagem aparece para verificar se há artefatos gráficos, desalinhamento ou cortes.
   - Atualize a coluna `Testado no Emulador` para `✅ Sim`.
