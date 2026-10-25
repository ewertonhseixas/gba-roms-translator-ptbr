# 📑 Relatório de Extração e Auditoria da ROM
**Jogo:** [NOME DO JOGO]  
**Código da ROM:** [ex: BSTE / AGB-BSTE-USA]  
**Tamanho da ROM:** [ex: 16.777.216 bytes (16 MB)]  
**Hash MD5 Original:** [ex: d41d8cd98f00b204e9800998ecf8427e]  
**Data da Extração:** [DATA_ATUAL]  
**Engenheiro / Agente:** Antigravity (Google DeepMind)  

---

## 🔍 1. Resumo da Varredura de Recursos

| Tipo de Recurso | Detectado? | Quantidade / Ocorrências | Formato / Compactação | Diretório de Destino |
| :--- | :---: | :---: | :--- | :--- |
| **Scripts de Texto / Diálogos** | ✅ Sim | [ex: 6 Lotes / 1.450 blocos] | PSI3 / Tabelas de Ponteiros | `ARQUIVOS md/` |
| **Fontes do Jogo** | ✅ Sim | [ex: 1 fonte VWF + 1 Fixa] | 1bpp / 2bpp tiles | `extracted/fonts/` |
| **Tabelas de Itens / Dados** | ✅ Sim | [ex: 480 itens e magias] | Estruturas binárias C de 32 bytes | `ARQUIVOS md/06-...` |
| **Imagens / Tiles com Texto** | ✅ Sim | [ex: 14 gráficos identificados] | Tiles 4bpp / 8bpp LZ77 | `fixes/graphics/` |
| **Fluxos de Vídeo / FMV** | [Sim / Não] | [ex: 1 abertura cinemática] | Mobiclip MOC5 / Actimagine | `extracted/video/` |
| **Bancos de Áudio / Vozes** | ✅ Sim | [ex: 128 faixas MIDI/PCM] | Sound Driver GBA Music Player 2000 | `extracted/audio/` |

---

## 🎬 2. Auditoria Específica de Vídeos e FMVs

> [!WARNING]
> ### ⚠️ Status de Vídeo no Cartucho:
> - **Presença de Vídeo:** [DETECTADO / NÃO DETECTADO]
> - **Engine / Codec:** [ex: Mobiclip Video Codec v5 / Actimagine / None]
> - **Offset do Container na ROM:** `0x08...` a `0x08...`
> - **Duração Estimada:** [ex: 45 segundos]
> - **Possui Falas / Vozes no Áudio:** [Sim / Não]
>
> **Estudo de Viabilidade de Legendas:**
> - [ ] **Opção A (Hardsub):** Viável se houver ferramentas de recompressão Mobiclip e se o bitrate couber no espaço livre da ROM.
> - [ ] **Opção B (Overlay de Texto / Softsub):** Requer injeção de hook na rotina de playback durante a interrupção de V-Blank.
> - [ ] **Sem Vídeo / Apenas Animação por Sprites:** Não requer legendagem de vídeo externa; os textos já estão nos scripts de diálogo padrão.

---

## 📊 3. Auditoria de Dados Estruturados (Game Data)

Tabelas e registros binários que alimentam mecânicas e status de jogo:

| Tabela de Dados | Offset Inicial na ROM | Qtd. de Registros | Tamanho do Registro (Bytes) | Campos de Texto Traduzíveis |
| :--- | :--- | :---: | :---: | :--- |
| **Tabela de Armas & Equip.** | `0x081D0000` | 240 | 32 bytes | Nome (8 bytes) + Descrição (ponteiro) |
| **Tabela de Itens Consumíveis** | `0x081D1E00` | 120 | 24 bytes | Nome (8 bytes) + Descrição (ponteiro) |
| **Tabela de Monstros / Chefes** | `0x081E4000` | 150 | 48 bytes | Nome do Monstro (10 bytes) |
| **Tabela de Magias & Habilidades** | `0x081E6000` | 64 | 20 bytes | Nome da Magia (8 bytes) + Efeito |

---

## 📐 4. Próximos Passos Obrigatórios

1. [ ] Calibrar o arquivo `estudo-de-metricas-e-caracteres.md` executando `metrics_analyzer.py`.
2. [ ] Validar o `02-glossario-e-terminologias.md` para travar termos centrais antes de iniciar os diálogos.
3. [ ] Preencher as biografias em `catalogo-de-personagens.md`.
4. [ ] Iniciar o servidor local `Iniciar_Validador.bat` para inspeção visual.
