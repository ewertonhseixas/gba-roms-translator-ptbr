# Relatório Técnico de Extração NDS: Tales of Hearts - Anime Movie Edition (Japan).nds

## 1. Cabeçalho e Binários Principais
- **Arquivo:** `Tales of Hearts - Anime Movie Edition (Japan).nds` (256.00 MB)
- **Título Interno:** `TOHHEARTSANM`
- **Game Code:** `CTUJ`
- **ARM9:** 432,924 bytes | **Overlays ARM9:** 31
- **ARM7:** 159,528 bytes | **Overlays ARM7:** 0

## 2. Inventário do NitroFS
- **Total de Arquivos:** 5,114
- **Tamanho Total Descompactado (NitroFS):** 235.19 MB

| Extensão | Quantidade | Observação |
| :--- | :---: | :--- |
| `(sem extensão)` | 4,449 | - |
| `.lvd` | 518 | - |
| `.dat` | 64 | Dados gerais / scripts |
| `.b` | 17 | - |
| `.ds3` | 16 | - |
| `.bin` | 16 | Dados binários / scripts / tabelas |
| `.mods` | 9 | - |
| `.ahx` | 7 | - |
| `.nftr` | 3 | Fonte bitmap/vetorial NDS (Nitro Font) |
| `.ncgr_lz` | 3 | - |
| `.nclr_lz` | 3 | - |
| `.nscr_lz` | 3 | - |
| `.cbb` | 1 | - |
| `.efg` | 1 | - |
| `.nsbmd` | 1 | - |
| `.txt` | 1 | - |
| `.sdat` | 1 | Áudio/Música (Sound Data) |
| `.wpd` | 1 | - |

## 3. Próximos Passos Recomendados
1. Extrair o NitroFS completo para `extracted/nitrofs/` para inspeção de textos e fontes.
2. Localizar arquivos de texto (em `.narc`, `.bin`, `.dat` ou `arm9.bin` / overlays).
3. Verificar se há fontes `.nftr` ou fontes customizadas para suporte a acentuação PT-BR.
4. Popular `ARQUIVOS md/` com os 5 Pilares Markdown e rodar `metrics_analyzer.py` + `qa_gate_hook.py`.
