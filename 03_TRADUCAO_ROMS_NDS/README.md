# 🎮 Ecossistema de Localização Nintendo DS (`03_TRADUCAO_ROMS_NDS`)

Este diretório segue a mesma arquitetura em **3 Tiers** e os **5 Pilares Markdown** do estúdio (`02_TRADUCAO_ROMS_GBA`), adaptados para a plataforma **Nintendo DS (NitroFS, ARM9/ARM7, Overlays, NARC, NFTR)**.

## 📁 Estrutura Padrão por Jogo (`jogos/<Nome_Do_Jogo>/`)
- `rom/` — ROM `.nds` original (somente leitura, nunca modificar in-place).
- `extracted/` — Conteúdo extraído do NitroFS, arquivos `.narc` descompactados, gráficos e scripts.
- `ARQUIVOS md/` — Os 5 Pilares Markdown de tradução:
  1. `02-glossario-e-terminologias.md`
  2. `03-mensagens-do-sistema.md`
  3. `06-itens-equipamentos-e-descricoes.md`
  4. `catalogo-de-personagens.md`
  5. Lotes sequenciais de diálogos (`08-`, `09-`, etc.)
- `docs/` — Relatórios técnicos (`relatorio-extracao.md`, métricas).
- `tools/` — Scripts de extração e reinserção específicos da engine do jogo.
- `build/` — ROM `.nds` compilada em PT-BR e patches (`.xdelta` / `.bps`).

## 🛠️ Ferramentas Disponíveis
- **Auditoria NDS (`_ferramentas_nds/nds_feature_detector.py`):**
  ```powershell
  python "03_TRADUCAO_ROMS_NDS/_ferramentas_nds/nds_feature_detector.py" "03_TRADUCAO_ROMS_NDS/jogos/<Jogo>/rom/<arquivo.nds>" -o "03_TRADUCAO_ROMS_NDS/jogos/<Jogo>/docs/relatorio-extracao.md"
  ```
- **Quality Gate, Métricas e Lotes (compartilhados de `02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/`):**
  - `qa_gate_hook.py` — Validação de limite de caracteres, tags `<br>`, neutralidade de gênero e orfandade.
  - `metrics_analyzer.py` — Calibração de Soft/Hard Limit.
  - `token_optimizer_batcher.py` — Fatiamento de lotes para tradução.
  - `image_text_auditor.py` — Controle de imagens com texto embutido.
