# 📜 Protocolo Mestre de Tradução e Localização de ROMs (PT-BR)
**Versão:** 1.2.0  
**Escopo Primário:** Game Boy Advance (GBA) & Consoles Retrô (SNES, Mega Drive, NDS, PS1)  
**Ambiente Integrado:** Suíte GBA ROMs Translator PT-BR & Antigravity (Google DeepMind)  
**Status:** Vital e Mandatório para todos os lotes de tradução e revisão  

---

## 🎯 1. Filosofia e Missão da Localização

A tradução de jogos clássicos em nosso framework não é uma mera substituição literal de palavras do idioma de origem (inglês/japonês) para o português, mas sim um processo de **localização cultural, técnica e imersiva**.

O objetivo primordial é entregar ao jogador de língua portuguesa:
1. **Imersão Narrativa Total:** Sensação de que o jogo foi concebido nativamente em português brasileiro.
2. **Respeito Estrito à Identidade da Obra:** Manutenção do tom emocional, cômico ou dramático idealizado pelos desenvolvedores originais.
3. **Harmonia com o Hardware:** Respeito absoluto aos limites de memória VRAM, largura de caixas de diálogo, tabelas de caracteres e variáveis da engine.

```mermaid
flowchart TD
    INPUT["📜 Script Original Extraído (.md)"] --> PRE["🎭 0. Pré-Tradução Obrigatória<br>(Catálogo de Personagens)"]
    PRE --> VOZ["🗣️ 1. Concordância de Voz & Perfil"]
    VOZ --> GENDER["⚧ 2. Neutralidade de Gênero Sistêmica"]
    GENDER --> CLEAN["🚫 3. Eliminação de Inglês & Nomes Próprios"]
    CLEAN --> COER["🔗 4. Coerência Narrativa & Glossário"]
    COER --> ABBREV["✂️ 5. Política de Abreviações"]
    ABBREV --> TERMS["💎 6. Ciclo de Termos Adaptados"]
    TERMS --> METRICS["📐 7. Ajuste às Métricas de Tela (GBA)"]
    METRICS --> QA["✅ 8. Funil de Validação & QA"]
    QA --> ROM_BUILD["🎮 Injeção na ROM PT-BR"]
```

---

## 🏛️ 2. Diretrizes Vitais de Tradução (Pilares Centrais)

### 2.1. Fase 0: Pré-Tradução Obrigatória — Criação do Catálogo de Personagens (`catalogo-de-personagens.md`)
> [!IMPORTANT]
> **REGRA DE OURO DA PRÉ-TRADUÇÃO:** É terminantemente **PROIBIDO** iniciar a tradução de qualquer lote de diálogo antes da criação, catalogação e aprovação do **Catálogo de Personagens (`catalogo-de-personagens.md`)**.

A tradução de diálogos sem o catálogo de personagens prévio gera invariavelmente textos homogêneos e robóticos, onde todos os falantes se expressam com a mesma cadência. A etapa de pré-tradução exige:

1. **Mapeamento Prévio de Todos os Falantes:**
   - Extrair a lista completa de IDs/falantes do script da ROM.
   - Cruzar os dados com fontes canônicas oficiais (manuais, wikis e artbooks) para resgatar a biografia, idade, temperamento e contexto social de cada um.
2. **Fixação Antecipada do Idioleto (*Character Voice*):**
   - Definir formalmente antes da primeira linha de tradução o grau de formalidade, os vícios de linguagem, bordões, expressões de carinho ou desprezo e metáforas associadas à ocupação do falante.
3. **Tratamento de Relações Interpessoais:**
   - Registrar no catálogo como cada personagem se dirige a seus pares (ex.: Bron chama aprendizes de "moleque" ou "garoto(a)"; Sugar trata o protagonista por apelidos carinhosos; Sanary trata rivais com arrogância aristocrática).
4. **Alimentação da Suite de Inteligência Artificial (*Token Economy*):**
   - O particionador [`token_optimizer_batcher.py`](../protocolo_extracao/tools/token_optimizer_batcher.py) extrai dinamicamente as fichas dos falantes do `catalogo-de-personagens.md` e as injeta no prompt da IA. Sem essa ficha prévia, o modelo alucina registros e quebra o tom dramático.

---

### 2.2. Localização por Classes, Papéis e Perfis de Personagens (*Character Voice*)
Cada personagem ou classe social deve possuir uma identidade vocal marcante, diferenciada por seu grau de instrução, idade, origem e papel na história:

*   **Mestres, Nobres e Autoridades:**
    *   *Tom:* Paternal, solene, experiente ou austero.
    *   *Linguagem:* Firme, elegante, vocabulário rico, sem gírias efêmeras. Artesãos usam metáforas de sua profissão (ex: "martelar", "temperar o aço", "fogo da forja").
*   **Protagonistas Jovens e Aprendizes:**
    *   *Tom:* Impulsivo, corajoso, determinado, bem-humorado.
    *   *Linguagem:* Coloquial limpa, ágil, direta, respeitosa com seus superiores e calorosa com aliados.
*   **Aliados Mágicos e Entidades Especiais:**
    *   Diferenciar rigorosamente criaturas solenes (linguagem arcaica ou matemática) de criaturas infantis, fadas emotivas (afetuosas, dengosas) ou guerreiros impetuosos (linguagem desafiadora e direta).
*   **Rivais:**
    *   Alternar entre arrogância nobre, competitividade franca e orgulho ferido, evitando caricaturas vazias.
*   **NPCs Comuns e Marinheiros:**
    *   Falam como o povo da cidade; linguagem informal, expressiva, acolhedora e prática.

---

### 2.3. Neutralidade de Gênero Sistêmica
> [!IMPORTANT]
> Em RPGs de GBA onde o jogador pode escolher o gênero do protagonista ou onde scripts de diálogo são reutilizados para múltiplos eventos, centenas de caixas de texto compartilham o **mesmo ponteiro de memória**.

O protocolo determina a utilização de **sintaxe neutra e epicena** para todas as referências diretas ao protagonista em caixas compartilhadas:

*   **Substituição de particípios e adjetivos por construções verbais:**
    *   ❌ *Incorreto:* "Você foi muito rápido e corajoso!"
    *   ✅ *Correto:* "Você agiu com muita rapidez e coragem!"
    *   ❌ *Incorreto:* "Você está cansado?"
    *   ✅ *Correto:* "O cansaço bateu?" / "Já está sem fôlego?"
    *   ❌ *Incorreto:* "Você é muito habilidoso!"
    *   ✅ *Correto:* "Você tem uma habilidade impressionante!"
*   **Agradecimentos Universais:**
    *   ❌ *Incorreto:* "Obrigado/a"
    *   ✅ *Correto:* "Meus agradecimentos!", "Agradeço de coração!", "Valeu!", "Muito obrigado!" (apenas quando o falante for inequivocamente homem fixo).
*   **Evitar Choque de Artigo com Variáveis:**
    *   ❌ *Incorreto:* "O {PLAYER} chegou!"
    *   ✅ *Correto:* "Olha só quem chegou: {PLAYER}!" / "{PLAYER} acaba de chegar!"

---

### 2.4. Eliminação Total do Inglês (Manter Apenas Nomes Próprios)
*   **Tolerância Zero:** Nenhum resquício de inglês deve permanecer em diálogos, comandos de combate, interfaces, tutoriais ou telas pós-batalha (*Victory, Level Up, Equip, Guard, Target, Miss, Run*).
*   **Critério para Nomes Próprios (Permanecem Originais):**
    *   Nomes de personagens fictícios (*Cleru, Pratty, Bron, Amar, Sanary, Varil, Lubert, etc.*).
    *   Nomes de continentes, reinos ou dimensões fantasia (*Silturn, Sapureth, Loreilal, Maetropa, Wystern*).
    *   Nomes geográficos puros (*Kagro, Mirana, Rugista*).
*   **Nomes Compostos com Tradução Obrigatória:**
    *   Elementos geográficos ou organizacionais compostos por palavras comuns **devem ser 100% traduzidos**:
        *   *Silver Guild* $\rightarrow$ **Guilda Prateada**
        *   *Gold Guild* $\rightarrow$ **Guilda Dourada**
        *   *Central Tower* $\rightarrow$ **Torre Central**
        *   *Marine Dungeon* $\rightarrow$ **Labirinto Marinho**
        *   *Cape Lighthouse* $\rightarrow$ **Farol do Cabo**
        *   *City of Swords* $\rightarrow$ **Cidade das Espadas**

---

### 2.5. Coerência Narrativa e Terminológica Unificada
*   **Fonte Única da Verdade:** Toda a tradução deve obedecer rigorosamente ao arquivo de Glossário do projeto (`02-glossario-e-terminologias.md`).
*   Se um item, material ou monstro foi nomeado no Capítulo 1, ele **jamais** poderá receber uma variação sinônima nos capítulos posteriores.
*   Termos de mecânica (nomes de status, atributos, elementos e técnicas) devem ser idênticos no diálogo, na interface de batalha e nas notificações do sistema.

---

### 2.6. Política Rígida de Abreviações
*   **Nos Diálogos (História, Conversas com NPCs, Eventos):**
    *   🚫 **PROIBIÇÃO ABSOLUTA.**
    *   É estritamente proibido o uso de abreviações técnicas ou internetês (`vc`, `pq`, `tb`, `q`, `p/`, `esp.`, `atq.`, `rec.`).
    *   Se a frase ultrapassar o limite da caixa, deve ser **reformulada com palavras mais concisas**, mantendo a naturalidade literária. Jamais mutile palavras em caixas de diálogo.
*   **Nas Telas de Menus, Equipamentos e Sistema:**
    *   ✅ **PERMITIDAS CONFORME TABELA OFICIAL.**
    *   Devido aos limites físicos de colunas (geralmente entre 8 e 16 caracteres para nomes e 2 linhas para descrições), abreviações são obrigatórias, mas devem seguir a tabela canônica do framework.

---

### 2.7. Ciclo de Vida dos Termos Adaptados
Termos conceituais próprios do universo do jogo que resultam em expressões longas em português devem seguir um ciclo de 3 fases para balancear ambientação e economia de caracteres:

| Fase | Contexto de Aplicação | Regra de Uso | Exemplo de Aplicação |
| :--- | :--- | :--- | :--- |
| **Fase 1: Introdução** | 1ª aparição, tutoriais, lore oficial e momentos solenes | Tradução completa e explicativa | *"Craftlord"* $\rightarrow$ **Lorde da Forja**<br>*"Craftknight"* $\rightarrow$ **Cavaleiro-Ferreiro**<br>*"Stray Summon"* $\rightarrow$ **Invocação Errante** |
| **Fase 2: Diálogo Comum** | Conversas cotidianas, ritmo rápido de ação | Forma adaptada e enxuta | **Lorde**, **Mestre**, **Ferreiro**, **Forjador**, **Errante**, **Guardião** |
| **Fase 3: Interface & Menus** | Listas de status, tabelas de títulos e menus | Forma sintetizada ou sigla oficial | **Lorde**, **Forjador**, **Errante** |

---

## ⚡ 3. Pilares Técnicos de Engenharia e Hardware

### 3.1. Métricas de Tela e Quebra de Linhas no GBA
*   **Hard Limit:** **36 caracteres por linha** (Teto operacional absoluto antes do corte visual pela moldura do GBA).
*   **Zonas de Segurança:**
    *   🟢 **1 a 32 caracteres:** Ideal (leitura fluida e sem risco).
    *   🟡 **33 a 35 caracteres:** Atenção (permitido apenas se contiver glifos finos como `i`, `l`, `t`, pontuação).
    *   🔴 **36+ caracteres:** **Crítico (Proibido)** — Exige quebra manual (`<br>`) ou reescrita concisa.
*   **Prevenção de Orfandade Textual:**
    *   Nunca isole monossílabos (`o`, `a`, `de`, `em`, `e`) no final de uma linha de diálogo quando a quebra seguinte separar o termo de seu núcleo.

---

### 3.2. Proteção Rígida de Tags e Variáveis da Engine
As variáveis dinâmicas injetadas pelo código ASM (`{PLAYER}`, `{PARTNER}`, `{SIBLING}`, `{VAR_2}`, `{VAR_4}`, `{MASTER}`) são intocáveis:
*   **Jamais altere a caixa, a grafia ou os delimitadores das chaves `{}` ou tags `<>`.**
*   Construa a frase ao redor da tag para que o resultado sonoro seja perfeito independentemente do valor preenchido em tempo de execução.

---

### 3.3. Tabela Canônica de Abreviações para Menus e Itens

| Conceito / Termo | Abreviação Padronizada | Exemplo Prático |
| :--- | :---: | :--- |
| **Ataque / Poder de Ataque** | `ATQ` | `ATQ +15` |
| **Defesa** | `DEF` | `DEF +8` |
| **Agilidade / Velocidade** | `AGI` | `AGI +5` |
| **Durabilidade** | `DUR` | `DUR 120/120` |
| **Pontos de Vida** | `HP` | `Recup. 50 HP` |
| **Recuperação / Recupera** | `Recup.` | `Recup. HP de aliado` |
| **Especial** | `Esp.` | `Técnica Esp.` |
| **Elemento / Elemental** | `Elem.` | `Ataque Elem. Fogo` |
| **Espada / Machado / Lança** | `Esp.` / `Mach.` / `Lanç.` | `Esp. de Ferro` |
| **Soqueira / Broca** | `Soq.` / `Broc.` | `Soq. de Aço` |
| **Minério** | `Min.` | `Min. de Ferro` |
| **Nível** | `Nv.` | `Nv. 25` |
| **Andar (Floor)** | `A` | `Torre Central 2A` |

---

### 3.4. Tipografia, Pontuação e Onomatopeias Brasileiras
*   **Reticências:** Sempre utilizar 3 pontos comuns (`...`) sem espaço antes.
*   **Onomatopeias:** Adaptar do japonês/inglês para o padrão cômico e expressivo brasileiro:
    *   *Sigh* $\rightarrow$ *Ufa...* / *Ai, ai...*
    *   *Gulp* $\rightarrow$ *Glup!*
    *   *Clank / Clang* $\rightarrow$ *Clang!* / *Trom!*
    *   *Gah! / Argh!* $\rightarrow$ *Argh!* / *Droga!*
    *   *Huh?* $\rightarrow$ *Hã?* / *Hein?*
    *   *Yikes!* $\rightarrow$ *Eita!* / *Caramba!*

---

## 🔄 4. Funil de Qualidade e Validação em 5 Etapas (QA)

Nenhum arquivo traduzido deve ser mesclado à ROM final sem cumprir o fluxo:

1.  **Etapa 0 — Pré-Tradução:** Conclusão e validação do Catálogo de Personagens (`catalogo-de-personagens.md`).
2.  **Etapa 1 — Tradução & Localização:** Tradução orientada pelo perfil, neutralidade e termos adaptados.
3.  **Etapa 2 — Validador Automatizado:** Execução das ferramentas de auditoria e métricas para detectar linhas acima de 35 caracteres, tags corrompidas e resquícios de inglês.
4.  **Etapa 3 — Revisão Textual Cruzada:** Leitura em voz alta para validar fluidez, pontuação e naturalidade dramática.
5.  **Etapa 4 — Teste In-Game:** Verificação em emulador ou port nativo para auditar quebras de linha e renderização gráfica real.

---

## 📌 5. Checklist Rápido de Liberação de Lote

Antes de aprovar qualquer lote traduzido:
- [ ] O **Catálogo de Personagens** foi previamente consultado e o idioleto do falante foi respeitado?
- [ ] Todas as linhas de diálogo respeitam a margem de **32 a 35 caracteres**?
- [ ] A linguagem soa natural para um falante nativo de português brasileiro?
- [ ] Frases compartilhadas funcionam perfeitamente sem flexão masculina indesejada?
- [ ] Todo texto em inglês foi eliminado (mantendo apenas nomes próprios)?
- [ ] As tags dinâmicas como `{PLAYER}` e `{PARTNER}` estão intactas?
- [ ] Diálogos estão livres de abreviações?
- [ ] Os termos adaptados foram introduzidos e usados de forma consistente?
