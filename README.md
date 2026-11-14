# 🕹️ ROMs Translation Framework & Protocol — Suíte de Processos e Engenharia

> [!NOTE]
> ### ⚖️ Aviso Legal & Filosofia do Repositório (Processos Apenas)
> - **Repositório Exclusivo de Processos e Ferramental:** Este repositório é um **framework de engenharia e processos**. Ele contém exclusivamente diretrizes metodológicas, especificações de protocolo, templates padronizados, scripts de automação e utilitários de validação.
> - **Nenhum Dado de Jogo Específico Versionado:** **Nenhum script traduzido, banco de dados de jogo específico, imagem comercial ou patch de jogo é mantido neste repositório**. Todas as pastas criadas para jogos individuais sob `jogos/` são mantidas estritamente em ambiente local e ignoradas pelo Git.
> - **Zero Tolerância para Distribuição de ROMs:** Este projeto **NÃO contém, não hospeda e NÃO disponibiliza nenhum arquivo de ROM comercial protegido por copyright**. O usuário opera localmente com suas próprias cópias legítimas.
> - **Direitos Autorais:** Marcas, nomes e elementos de propriedades intelectuais originais citados a título de estudo pertencem aos seus respectivos estúdios e publicadores (Nintendo, Banpresto, Konami, Atlus, Capcom, etc.).

---

Este repositório reúne a metodologia oficial, os protocolos de extração estruturada e as ferramentas modulares para localização e tradução de ROMs retrô (com foco primário em **Game Boy Advance** e arquitetura extensível para **SNES, Mega Drive, NDS e PS1**), otimizados para fluxo de trabalho de alta performance e **economia de tokens** com Inteligência Artificial (Google Antigravity / DeepMind).

---

## 📂 Arquitetura do Repositório

O repositório é enxuto e preserva apenas o pipeline operacional de desenvolvimento e a hierarquia multi-agente do **GBA Localization Studio**:

```
gba-roms-translator-ptbr/
│
├── 📁 .agents/                   # 🏛️ GBA LOCALIZATION STUDIO (Arquitetura em 3 Tiers)
│   ├── 📁 agents/                # 7 Personas Especializadas (Direção, Liderança e Execução)
│   │   ├── gba-localization-director.md    # Tier 1: Showrunner & Guardião do Glossário/Catálogo
│   │   ├── gba-rom-hacking-director.md     # Tier 1: Engenharia ARM7TDMI, Ponteiros, VWF & Build
│   │   ├── gba-narrative-lead.md           # Tier 2: Character Voice & Fatiamento Cirúrgico
│   │   ├── gba-graphics-ui-lead.md         # Tier 2: Auditoria de Tiles/PNGs, Paletas & Glifos PT-BR
│   │   ├── gba-dialogue-translator.md      # Tier 3: Tradução Dramatúrgica (≤35 chars, Gênero Neutro)
│   │   ├── gba-system-arsenal-translator.md# Tier 3: UI, Menus, Itens & Abreviações Canônicas
│   │   └── gba-strict-qa-auditor.md        # Tier 3: Quality Gate Implacável & Revisão Pente-Fino
│   │
│   └── 📁 skills/                # ⚡ 5 Workflows Acionáveis (Skills)
│       ├── gba-new-game-kickoff/ # Kickoff estruturado de nova ROM
│       ├── gba-character-bible/  # Fase 0: Mapeamento de falantes e Character Voice
│       ├── gba-translate-sprint/ # Sprint de tradução com Contexto Cirúrgico / Swarm
│       ├── gba-qa-gate/          # Funil de auditoria automatizada + revisão humana
│       └── gba-rom-build-verify/ # Compilação segura de ROM, gráficos e patch IPS/BPS
│
├── 📁 protocolo_extracao/        # 📜 PROTOCOLO MESTRE & ENGENHARIA DE EXTRAÇÃO
│   ├── PROTOCOLO_MESTRE_EXTRACAO.md # Manual técnico integral (Normas, VRAM, Multi-Console)
│   ├── README.md                 # Guia de início rápido da suíte de extração
│   │
│   ├── 📁 templates/             # Modelos oficiais prontos (.md)
│   │   ├── 02-glossario-e-terminologias.template.md
│   │   ├── 03-mensagens-do-sistema.template.md
│   │   ├── 06-itens-equipamentos-e-descricoes.template.md
│   │   ├── catalogo-de-personagens.template.md
│   │   ├── estudo-de-metricas-e-caracteres.template.md
│   │   ├── controle-de-imagens-com-texto.template.md
│   │   └── relatorio-extracao.template.md
│   │
│   └── 📁 tools/                 # Ferramentas CLI em Python (Core do Protocolo)
│       ├── metrics_analyzer.py        # Análise estatística de limites de caracteres e overflow
│       ├── qa_gate_hook.py            # Quality Gate automatizado (overflow, gênero, órfãs, tags)
│       ├── rom_feature_detector.py    # Fingerprint, detecção de compressão e vídeos (Mobiclip)
│       ├── image_text_auditor.py      # Catalogação e auditoria de integridade de imagens/paleta
│       └── token_optimizer_batcher.py # Fatiador com injeção cirúrgica de contexto (Token Economy)
│
├── 📁 protocolo_traducao/        # ✍️ PROTOCOLO MESTRE DE TRADUÇÃO & LOCALIZAÇÃO
│   ├── PROTOCOLO_MESTRE_TRADUCAO.md      # Diretrizes canônicas (Pré-tradução, Vozes, QA)
│   ├── GLOSSARIO_GLOBAL_SUMMON_NIGHT.md  # Fonte Única da Verdade para os 13 jogos da franquia
│   └── README.md                         # Guia de diretrizes de escrita e adaptação
│
├── 📁 jogos/                     # Workspace local para projetos de jogos
│   │
│   └── 📁 _MODELO_NOVO_JOGO/    # Template mestre padronizado para iniciar novos projetos
│       ├── ARQUIVOS md/         # Modelos pré-carregados de Glossário, Sistema, Itens e Catálogo
│       ├── docs/                # Relatório técnico e protocolo de tradução padrão
│       ├── releases/            # Pasta destino de patches locais
│       ├── rom/                 # Local para inserção da ROM original local
│       ├── tools/               # Validador web integrado (App interativo + UI)
│       ├── Compilar_ROM_PTBR.bat        # Atalho de build local
│       ├── Iniciar_Validador_Traducao.bat # Atalho para interface web local
│       └── README.md            # Guia passo a passo do novo jogo
│
├── AGENTS.md                    # Regras globais de governança por escopo de arquivo (Path-Scoped)
├── .gitignore                   # Blindagem estrita (ignora jogos/*, ROMs, zips, saves e backups)
└── README.md                    # Esta documentação
```

---

## 🏛️ 0. GBA Localization Studio (Arquitetura Multi-Agente em 3 Tiers)

Inspirado na organização do *Claude-Code-Game-Studios* e integrado nativamente aos Protocolos Mestres deste projeto, o repositório opera como um **Estúdio de Localização em 3 Tiers** governado por [`AGENTS.md`](AGENTS.md):

| Tier | Agente (`.agents/agents/`) | Papel no Estúdio |
| :---: | :--- | :--- |
| **Tier 1 (Direção)** | `gba-localization-director` | **Showrunner e Diretor de Localização:** Guardião da Fase 0 obrigatória, do Catálogo de Personagens e do Glossário Global. |
| **Tier 1 (Direção)** | `gba-rom-hacking-director` | **Diretor de Engenharia e ROM Hacking:** Arquitetura ARM7TDMI, tabelas de ponteiros, fontes VWF/monoespaçadas, compressão BIOS e build IPS/BPS. |
| **Tier 2 (Liderança)** | `gba-narrative-lead` | **Líder de Narrativa e Dramaturgia:** Constrói a biografia híbrida, define o *Character Voice* e fatia lotes com `token_optimizer_batcher.py`. |
| **Tier 2 (Liderança)** | `gba-graphics-ui-lead` | **Líder de Gráficos, Fontes e UI:** Audita PNGs/tiles com `image_text_auditor.py`, protege o índice 0 de transparência e desenha glifos acentuados. |
| **Tier 3 (Execução)** | `gba-dialogue-translator` | **Tradutor Dramatúrgico de Diálogos:** Traduz lotes narrativos (1–32 chars ideal, máx 35 chars, `<br>`, neutralidade de gênero para `{PLAYER}`, zero abreviações). |
| **Tier 3 (Execução)** | `gba-system-arsenal-translator` | **Tradutor de Sistema, Menus e Arsenal:** Traduz `03-` e `06-` aplicando 0% de inglês residual e a Tabela Canônica de Abreviações. |
| **Tier 3 (Execução)** | `gba-strict-qa-auditor` | **Auditor Implacável de QA:** Executa o Quality Gate automatizado (`qa_gate_hook.py` + `metrics_analyzer.py`) e inspeção pente-fino. |

### ⚡ Workflows Acionáveis (`.agents/skills/`)
- **`gba-new-game-kickoff`**: Disseca uma nova ROM do zero, gera o relatório técnico e instancia a estrutura Markdown.
- **`gba-character-bible`**: Executa a Fase 0 obrigatória antes da tradução, mapeando falantes e criando o `catalogo-de-personagens.md`.
- **`gba-translate-sprint`**: Orquestra sprints de tradução em série ou enxame (*Swarm*) com Contexto Cirúrgico e validação imediata.
- **`gba-qa-gate`**: Roda o funil de qualidade automatizado e corrige overflows (>35 chars), choques de gênero, órfãs e tags.
- **`gba-rom-build-verify`**: Audita imagens editadas, compila a ROM PT-BR e gera o patch IPS/BPS pronto para teste.

---

## ⚡ 1. O Protocolo Mestre de Extração e Tradução

O **[Protocolo Mestre de Extração](protocolo_extracao/PROTOCOLO_MESTRE_EXTRACAO.md)** padroniza todo o ciclo de vida da localização de uma ROM em 5 pilares fundamentais:

```mermaid
flowchart TD
    ROM["🎮 ROM Original Local (.gba)"] --> DETECT["🔍 1. Fingerprint & Detecção de Recursos<br>(rom_feature_detector.py)"]
    DETECT --> EXTRACT_TXT["📜 Extração de Textos & Ponteiros"]
    DETECT --> EXTRACT_IMG["🖼️ Extração de Gráficos e Tiles"]
    DETECT --> DETECT_VID["🎬 Varredura de Vídeos e FMVs"]
    DETECT --> EXTRACT_DATA["📊 Extração de Tabelas de Dados"]
    
    EXTRACT_TXT --> METRICS["📐 2. Estudo de Métricas de Caracteres<br>(metrics_analyzer.py)"]
    EXTRACT_TXT --> CHAR_CAT["🎭 3. Catálogo de Personagens (In-Game + Web)"]
    EXTRACT_IMG --> IMG_CTRL["📋 4. Planilha de Controle de Imagens<br>(image_text_auditor.py)"]
    
    METRICS & CHAR_CAT & IMG_CTRL --> CHUNKING["⚡ 5. Fatiamento Cirúrgico / Token Economy<br>(token_optimizer_batcher.py)"]
    CHUNKING --> VALIDATOR["✅ Validação Visual no Navegador<br>(translation_validator_app.py)"]
```

### Os 5 Pilares do Protocolo:
1. **Textos Estruturados em Markdown:** Todos os textos do jogo são organizados em tabelas compatíveis com o validador web interativo, mantendo arquivos essenciais obrigatórios: Glossário (`02-`), Mensagens de Sistema (`03-`), Itens e Equipamentos (`06-`) e Lotes sequenciais de história.
2. **Estudo de Métricas e Limites de Linha:** Análise matemática da largura em pixels das caixas de diálogo e das fontes do jogo. Define zonas de segurança: **Ideal (1 a 32 chars)**, **Soft Limit (33 a 35 chars)** e **Hard Limit (36+ chars / overflow)**, com quebra manual estrita via `<br>`.
3. **Catálogo de Personagens com Biografia Híbrida:** Mescla dados extraídos da ROM com pesquisa em fontes canônicas oficiais (artbooks, wikis) para balizar o **Tom de Voz**, idioleto, registro de fala (formal, coloquial, rústico, sarcástico) e maneirismos.
4. **Imagens com Texto Auditadas:** Rastreamento rigoroso de gráficos que contêm textos desenhados (Title, Game Over, Menus). O protocolo audita resoluções em pixels e proíbe o uso do índice 0 da paleta (transparência de hardware).
5. **Varredura de Vídeos e FMVs:** Detecção de codecs de vídeo (Mobiclip `MOC4`/`MOC5`, Actimagine) com estudo prévio de viabilidade entre *hardsub* ou *softsub overlay*.

---

## ✍️ 2. O Protocolo Mestre de Tradução e Localização

O **[Protocolo Mestre de Tradução](protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md)** estabelece as normas gramaticais, literárias e de engenharia para assegurar máxima qualidade nas adaptações em Português Brasileiro:

1. **Localização por Classes e Perfis (*Character Voice*):** Linguagem adaptada ao papel social de cada personagem (Mestres com linguagem solene/artesanal, aprendizes enérgicos, entidades mágicas distintas).
2. **Neutralidade de Gênero Sistêmica:** Redação epicena e impessoal para diálogos do protagonista que compartilham o mesmo ponteiro de script entre avatares masculino e feminino, eliminando choques de concordância.
3. **Eliminação Integral do Inglês:** 100% de menus, itens, combate e diálogos traduzidos, mantendo estritamente nomes próprios de pessoas e regiões de fantasia.
4. **Coerência Terminológica:** Fonte única da verdade ancorada no Glossário unificado (`02-glossario-e-terminologias.md`).
5. **Política Rígida de Abreviações:** Proibição absoluta de abreviações telegráficas nos diálogos da história; uso permitido e tabelado apenas em menus e descrições curtas de itens.
6. **Ciclo de Termos Adaptados:** Termos extensos do universo do jogo são introduzidos com sua tradução completa (*ex: Lorde da Forja, Cavaleiro-Ferreiro*) e sintetizados nos diálogos corriqueiros (*ex: Lorde, Ferreiro*) para economia de caracteres.
7. **Funil de QA em 4 Etapas:** Tradução $\rightarrow$ Validação de Métricas e Tags $\rightarrow$ Revisão Textual Cruzada $\rightarrow$ Teste In-Game no emulador/hardware.

---

## 💡 3. Estratégia de Economia de Tokens (*Token Economy*)

Dumps brutos de ROMs contendo milhares de linhas descontextualizadas geram desperdício massivo de tokens e alucinações terminológicas em Modelos de Linguagem (LLMs). O utilitário [`token_optimizer_batcher.py`](protocolo_extracao/tools/token_optimizer_batcher.py) resolve isso aplicando o **Princípio do Contexto Cirúrgico**:

* **Fatiamento em Lotes Ideais:** Divide os diálogos em blocos compactos de 30 a 50 caixas de fala.
* **Injeção Dinâmica de Glossário:** O prompt contém **apenas** os termos que de fato aparecem no lote sendo traduzido.
* **Personagens Ativos Apenas:** Apenas os perfis dos personagens que falam no trecho são incluídos no contexto.
* **Retorno em Tabela Compacta:** O modelo devolve apenas as colunas de tradução indexadas, alcançando até **75% de economia de tokens** por interação.

---

## 🛠️ 4. Catálogo das Ferramentas CLI do Framework

Todas as ferramentas foram desenvolvidas em **Python 3** (sem dependências externas obrigatórias):

| Ferramenta | Comando de Exemplo | Finalidade |
| :--- | :--- | :--- |
| **`rom_feature_detector.py`** | `python protocolo_extracao/tools/rom_feature_detector.py rom/jogo.gba -o docs/relatorio.md` | Detecta serial oficial, compressões BIOS (LZ77/Huffman), tabelas de ponteiros e vídeos FMV. |
| **`metrics_analyzer.py`** | `python protocolo_extracao/tools/metrics_analyzer.py -d "ARQUIVOS md" -g "Jogo" -l 36` | Analisa limites de caracteres, quebras `<br>`, calcula médias e sinaliza falas com risco de overflow. |
| **`qa_gate_hook.py`** | `python protocolo_extracao/tools/qa_gate_hook.py "ARQUIVOS md" -l 35` | Quality Gate automatizado que bloqueia overflows (>35 chars), choques de gênero em `{PLAYER}`, abreviações proibidas, órfãs no fim de linha e tags dessincronizadas. |
| **`image_text_auditor.py`** | `python protocolo_extracao/tools/image_text_auditor.py -d "extracted/graphics" -o "controle-imagens.md"` | Mapeia dimensões e paletas de PNGs e audita imagens editadas antes da reinjeção na ROM. |
| **`token_optimizer_batcher.py`** | `python protocolo_extracao/tools/token_optimizer_batcher.py "ARQUIVOS md/08-dialogos.md" -s 35` | Gera prompts enxutos de alta densidade informacional para tradução assistida por IA. |
| **`translation_validator_app.py`** | `python tools/translation_validator_app.py` *(dentro do projeto)* | Servidor web local com interface visual simulando a tela de diálogo do GBA em tempo real. |

---

## 🚀 5. Como Iniciar um Novo Projeto de Tradução (Localmente)

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/ewertonhseixas/gba-roms-translator-ptbr.git
   cd gba-roms-translator-ptbr
   ```

2. **Crie a pasta do seu novo jogo duplicando o template:**
   * Copie a pasta `jogos/_MODELO_NOVO_JOGO/` para dentro de `jogos/` com o nome do seu jogo (ex: `jogos/Meu_Jogo_GBA/`).
   * *(Nota: Graças ao `.gitignore`, a nova pasta ficará ativa apenas no seu computador local, sem poluir o repositório).*

3. **Insira sua ROM original:**
   * Coloque a sua cópia legal da ROM `.gba` na pasta `jogos/Meu_Jogo_GBA/rom/`.

4. **Execute as etapas do Protocolo:**
   * Rode o `rom_feature_detector.py` para gerar o relatório de auditoria inicial em `docs/relatorio-extracao.md`.
   * Realize a extração dos textos para os templates Markdown em `ARQUIVOS md/`.
   * Calibre as medidas executando `metrics_analyzer.py`.
   * Traduza utilizando o validador interativo (`Iniciar_Validador_Traducao.bat`) ou com auxílio do particionador de IA (`token_optimizer_batcher.py`).
   * Compile a ROM e o patch localmente com `Compilar_ROM_PTBR.bat`.

---

## 🌐 6. Extensibilidade Multi-Console

Embora o Game Boy Advance seja o foco primordial da arquitetura atual, a suíte foi projetada em camadas desacopladas para permitir extensão direta para outros consoles clássicos:

* **Super Nintendo (SNES):** Mapeamento de 24 bits (LoROM/HiROM), fontes 1bpp/2bpp e compressões HAL/Nintendo LZ.
* **Mega Drive / Genesis:** Arquitetura Motorola 68000 Big-Endian, compressões Nemesis/Kosinski e paletas de 64 cores.
* **Nintendo DS (NDS):** Sistema de arquivos interno NARC/SDAT, fontes nativas NFTR e vídeos Mobiclip VX.
* **PlayStation (PS1):** Sistema de arquivos ISO 9660, texturas TIM, vídeos MDEC (STR) e ponteiros Little-Endian MIPS.
