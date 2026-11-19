# 🎮 GBA Localization Studio — Regras Globais de Engenharia & Tradução

Este repositório opera sob a arquitetura de estúdio em **3 Tiers** inspirada no *Claude-Code-Game-Studios*, governada pelo **[Protocolo Mestre de Extração](02_TRADUCAO_ROMS_GBA/protocolo_extracao/PROTOCOLO_MESTRE_EXTRACAO.md)** e pelo **[Protocolo Mestre de Tradução](02_TRADUCAO_ROMS_GBA/protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md)**.

## 🏛️ 1. Hierarquia de Personas e Agentes (`.agents/agents/`)
- **Tier 1 (Direção):**
  - `gba-localization-director`: Showrunner, guardião do Glossário Global, do Catálogo de Personagens e da Fase 0 obrigatória.
  - `gba-rom-hacking-director`: Arquiteto de engenharia reversa, ponteiros ARM7TDMI, fontes VWF e compilação de ROMs.
- **Tier 2 (Liderança de Pipeline):**
  - `gba-narrative-lead`: Criador das fichas de voz (*Character Voice*) e fatiador de contexto cirúrgico (`token_optimizer_batcher.py`).
  - `gba-graphics-ui-lead`: Auditor de imagens com texto (`image_text_auditor.py`), fontes acentuadas e proteção do índice 0 de paleta.
- **Tier 3 (Especialistas de Execução):**
  - `gba-dialogue-translator`: Tradutor dramatúrgico de lotes de história (1-32 chars/linha ideal, max 35 chars, gênero neutro para `{PLAYER}`, zero abreviações).
  - `gba-system-arsenal-translator`: Especialista em UI, menus e equipamentos (`03-` e `06-`), utilizando a Tabela Canônica de Abreviações.
  - `gba-strict-qa-auditor`: Auditor implacável que executa `qa_gate_hook.py` e `metrics_analyzer.py`.

## 🔒 2. Regras Invioláveis por Escopo de Arquivo (Path-Scoped Guidelines)

### A. Ao editar Lotes de Diálogos de História (`**/ARQUIVOS md/*.md`, exceto `02-`, `03-`, `06-`)
1. **Fase 0 Obrigatória:** Consulte sempre `catalogo-de-personagens.md` e `02-glossario-*.md` antes de traduzir.
2. **Métricas de Linha GBA:** Separe linhas na mesma caixa exclusivamente com `<br>`. Mantenha cada linha entre **1 e 32 caracteres** (Zona Ideal) ou no máximo **35 caracteres** (Soft Limit). **36+ caracteres é proibido (Hard Limit).**
3. **Neutralidade de Gênero Sistêmica:** Jamais use adjetivos masculinos/femininos diretos para `{PLAYER}` (ex: proibido *"cansado"*, *"pronto"*, *"corajoso"*, *"bem-vindo"*, *"obrigado/a"*). Use substantivos e locuções neutras (*"O cansaço bateu?"*, *"Tudo pronto?"*, *"Você agiu com muita coragem!"*, *"Boas-vindas!"*, *"Agradeço de coração!"*).
4. **Proibição Absoluta de Abreviações:** Nunca use `vc`, `tb`, `pq`, `atq.`, `esp.` em diálogos narrativos.
5. **Prevenção de Orfandade:** Nunca deixe artigos ou preposições curtas (`o`, `a`, `de`, `do`, `da`, `em`, `e`, `que`) isolados no fim de uma linha antes de `<br>`.

### B. Ao editar Menus e Equipamentos (`**/03-mensagens-do-sistema.md`, `**/06-itens-*.md`)
1. Elimine 100% do inglês (*Victory -> Vitória*, *Equip -> Equipar*, *Guard -> Defesa*, *Miss -> Errou*).
2. Utilize apenas as abreviações canônicas quando houver restrição de largura: `ATQ`, `DEF`, `AGI`, `DUR`, `HP`, `Recup.`, `Esp.`, `Elem.`, `Mach.`, `Lanç.`, `Soq.`, `Broc.`, `Min.`, `Nv.`, `A` (Andar).

### C. Quality Gate Obrigatório Pós-Edição
- Sempre que concluir a tradução ou edição de um arquivo `.md`, execute o Quality Gate antes de dar a tarefa por encerrada:
  `python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/qa_gate_hook.py" "<caminho_do_arquivo.md>" -l 35`
