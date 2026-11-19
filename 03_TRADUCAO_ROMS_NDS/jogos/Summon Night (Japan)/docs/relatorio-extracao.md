# Relatório Técnico de Extração NDS: Summon Night (Japan).nds

## 1. Cabeçalho e Binários Principais
- **Arquivo:** `Summon Night (Japan).nds` (128.00 MB)
- **Título Interno:** `SUMMONNIGHT1`
- **Game Code:** `YSMJ`
- **ARM9:** 515,176 bytes | **Overlays ARM9:** 3
- **ARM7:** 159,160 bytes | **Overlays ARM7:** 0

## 2. Inventário do NitroFS
- **Total de Arquivos:** 3,323
- **Tamanho Total Descompactado (NitroFS):** 72.25 MB

| Extensão | Quantidade | Observação |
| :--- | :---: | :--- |
| `.narc` | 3,176 | Arquivo contêiner (Nitro Archive) |
| `.rtz` | 85 | - |
| `.acmz` | 57 | - |
| `.ini` | 2 | - |
| `.nftr` | 2 | Fonte bitmap/vetorial NDS (Nitro Font) |
| `.sdat` | 1 | Áudio/Música (Sound Data) |

## 3. Próximos Passos Recomendados
1. Extrair o NitroFS completo para `extracted/nitrofs/` para inspeção de textos e fontes.
2. Localizar arquivos de texto (em `.narc`, `.bin`, `.dat` ou `arm9.bin` / overlays).
3. Verificar se há fontes `.nftr` ou fontes customizadas para suporte a acentuação PT-BR.
4. Popular `ARQUIVOS md/` com os 5 Pilares Markdown e rodar `metrics_analyzer.py` + `qa_gate_hook.py`.
