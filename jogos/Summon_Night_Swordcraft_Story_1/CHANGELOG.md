# Changelog — Tradução PT-BR: Summon Night - Swordcraft Story (GBA)

Todas as alterações e lançamentos significativos deste projeto serão documentados neste arquivo a partir da **v0.1**.

---

## [v0.2.5] — 2026-10-23 (Revisão da Pasta Fixes & Localização Canônica de Termos e Itens)

### ✨ Destaques da Versão (Rumo à v0.3)
- **Incorporação Completa dos 21 Fixes dos Screenshots (`fixes/correção parte 1`):**
  - **Concordâncias e Neutralização de Gênero do Protagonista:** Ajustado o diálogo de determinação na Cerimônia de Abertura (`#1604 [99..101]`) para neutralidade impecável (*"Vou provar a todos em Wystern que mereço alcançar o posto de grande Lorde Forjador"*), eliminando falas femininas acidentais ao jogar com Cleru (*"digna / próxima"*).
  - **Correção de Pronomes e Falas de Invocação:** Linha de Rasho ao ser invocado (`#1609 [63]`) corrigida de *"aí parada me encarando"* para *"aí só me encarando"*, válida para ambos os sexos. Resposta plural de Rasho (`#1695 [99]`) corrigida para o singular *"Chega disso! Enfim,"*.
  - **Alinhamento do Menu de Salvamento e Pausa:**
    - Slot de save ajustado de `Guilda Prateada 2A` (18 caracteres) para `G. Prateada 2A` (14 caracteres), evitando transbordamento no limite de 16 tiles.
    - String de `Home` atualizada com espaço de respiro (`Minha Casa `), evitando colagem de caracteres na interface de pausa.
  - **Revisão de Diálogos e Coerência Local:**
    - Diálogo de vício em curry (`#0259 [3..5]`) reescrito com fluidez natural (*"Meu filho é tão viciado em curry que quero ajudá-lo a largar esse hábito de uma vez"*).
    - Fala de Razzy sobre Fera Guardiã (`#0310 [13]`) corrigida de *"comprou uma Guardian Beast"* para *"conseguiu uma Fera Guardiã"*.
    - Reestruturação da explicação de combate de Razzy (`#0310 [35..36]`), removendo pontuações quebradas.
    - Diálogo de parceria de Sanary (`#0301 [134..136]`) e falas marinhas de Pratty (`#1655 [19]`) localizados naturalmente (*"Dá para ver o oceano daqui…"*).
    - Fala de treino do Mestre Bron (`#1657 [133]`) corrigida de *"Vou ensinar a cê"* para *"Certo. Vou te ensinar"*.
- **Catálogo de Itens, Minérios e Materiais 100% Traduzido (`06-itens`):**
  - Identificada e solucionada a omissão de ponteiros de descrição na Seção 6 de materiais.
  - Traduzidos todos os 171 itens, acessórios, minérios, materiais de forja e itens-chave, com descrições concisas e precisas (ex: `Cálice sem Fundo` -> *"Material inicial de Água"*, `Bandagem` -> *"Recupera 150 HP"*, sem truncamento).
- **Tradução Global de Terminologia e Universo:**
  - `Craftlord` / `Craftlords` -> `Lorde Forjador` / `Lordes Forjadores` (e `Lorde [Nome]` quando título).
  - `Craftknight` / `Craftknights` -> `Cavaleiro Forjador` / `Cavaleiros Forjadores` (ou `forjador(es)` quando natural).
  - `Guardian Beast` / `Guardian Beasts` -> `Fera Guardiã` / `Feras Guardiãs`.
  - `Summon Creature` / `Summon Beasts` -> `Criatura Invocada` / `Feras Invocadas`.
  - `Stray Summon(s)` -> `Criatura(s) Errante(s)`.
  - `Dungeon / calabouço` -> `Labirinto` (ex: `Labirinto Marinho`).
  - `Central Tower` -> `Torre Central`, `Silver Guild` -> `Guilda Prateada`, `Gold Guild` -> `Guilda Dourada`, `City of Swords` -> `Cidade das Espadas`.
- **Regra Rígida de <= 35 Caracteres por Linha & Zero Abreviações:**
  - Auditados todos os 24 arquivos de diálogo do jogo: **zero linhas ultrapassam 35 caracteres** (over_35 = 0).
  - Eliminadas abreviações coloquiais excessivas (`cê`, `cês`, `p/`, `c/`, `etc.`).
  - Preservados 100% de nomes próprios (Cleru, Pratty, Amariss, Sanary, etc.), armas e monstros do bestiário.
- **Sincronização Bidirecional dos Arquivos de História:**
  - Edições manuais do usuário em `22-historia-prologo-e-cap01-abertura-e-chaves.md` incorporadas e sincronizadas com `10-dialogos` e `11-dialogos`.

### 📦 Arquivos do Lançamento
- **ROM Compilada:** `rom/Summon Night - Swordcraft Story (PT-BR).gba` (8.388.608 bytes)
- **Patch IPS Oficial:** `releases/Summon Night - Swordcraft Story (PT-BR) v0.2.5.ips` (1.103.003 bytes)

---

## [v0.2] — 2026-10-22 (Revisão Geral e Localização Completa)

### ✨ Destaques da Versão
- **Localização Completa dos 12 Dias & Pós-Jogo:**
  - 100% da história principal, explorações diárias, eventos noturnos, torneios do Coliseu, masmorras opcionais e múltiplos finais revisados em PT-BR natural.
- **Auditoria Rigorosa de Diálogos ($\le 35$ Caracteres por Linha):**
  - Todas as 28.993 linhas de diálogo dos 661 scripts PSI3 foram auditadas e formatadas com limite estrito de $\le 35$ caracteres por linha renderizada, garantindo zero transbordamento (*overflow*) ou cortes de texto nas caixas de diálogo do GBA.
- **Harmonização de Terminologia e Nomes:**
  - **Deigley:** Padronização completa para *"de Deigley"* (*"Soldados de Deigley"*, *"Tropas de Deigley"*, etc., eliminando arcaísmos e inconsistências).
  - **Andares:** Unificação do indicador de pavimentos e pisos para o formato brasileiro (`1A`, `2A`, `1º Andar`, `2º Andar`, etc., eliminando notações em inglês como `1F`, `2F`).
  - **Tipos de Armas:** Padronização canônica (*Sword Type, Axe Type, Spear Type, Knuckle Type, Drill Type*), corrigindo equívocos de tradução mecânica (como "exercício" ou "furadeira" para a classe Drill).
  - **Concordâncias & Gênero:** Ajustes em diálogos com Sanary, parceiros invocados e NPCs locais.
- **Tabelas e Scripts:**
  - 100% das tabelas Markdown dos 6 Lotes auditadas com integridade estrutural perfeita (5 colunas) e marcadores de validação.

### 📦 Arquivos do Lançamento
- **ROM Compilada:** `rom/Summon Night - Swordcraft Story (PT-BR).gba` (8.388.608 bytes)
- **Patch IPS Oficial:** `releases/Summon Night - Swordcraft Story (PT-BR) v0.2.ips`

---

## [v0.1] — 2026-10-21 (Primeira Versão Jogável / Beta Inicial)

### ✨ Destaques da Versão
- **Interface e Menus 100% Funcionais em PT-BR:**
  - Submenus de pausa traduzidos: *Equipamento, Suporte, Item, Magia, Arma, Status, Lista, Suspender Jogo*.
  - Menus de batalha, forja, lojas e diálogos de sistema localizados.
  - Tradução dos 38 nomes de locais do mapa (ex: *Wystern Baixa Minha Casa*).
  - Correção e suporte do indicador de andar (`Casa 2A` em vez de `Casa2F`).
- **Catálogos e Tabelas Estáticas:**
  - 306 entradas de Armas, Técnicas/Magias e Itens com nomes e descrições traduzidos.
  - 97 monstros do Bestiário localizados.
- **Diálogos da História e Eventos (Scripts PSI3):**
  - 661 scripts únicos compilados com recalibração de ponteiros e opcodes (28.993 linhas traduzidas incorporadas na ROM).
  - Abertura, Cerimônia do Dia 1 e Invocação da Fera Guardiã revisadas (com ajuste de quebras de linha `<br>`).
- **Tipografia e Fonte Especial PT-BR:**
  - Injeção completa dos 24 glifos acentuados PT-BR (`á, à, ã, â, é, ê, í, ó, ô, õ, ú, ç...`) diretamente no banco de fontes da BIOS/ROM (`BIT\0` @ `0x08707808`).
  - Patch da engine em `0x08009E32` (NOP) para renderização proporcional de 12x12 px.
- **Diretriz de Design & Fidelidade Visual:**
  - Preservação da arte original em inglês dos cabeçalhos gráficos (`COMMAND`, `STATUS`, `MONEY`, `MATERIAL`, `WEAPON`, `ITEM`, `EVENT ITEM`, `PLAY TIME`, `PLACE`) e dos sprites da tela de título (`PRESS START`, `NEW GAME`, `CONTINUE`), mantendo a estética clássica de fábrica.

### 📦 Arquivos do Lançamento
- **ROM Compilada:** `rom/Summon Night - Swordcraft Story (PT-BR).gba` (8.388.608 bytes)
- **Patch IPS:** `releases/Summon Night - Swordcraft Story (PT-BR) v0.1.ips`
