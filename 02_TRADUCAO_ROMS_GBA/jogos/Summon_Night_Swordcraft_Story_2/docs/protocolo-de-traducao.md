# 📜 Protocolo Oficial de Tradução e Localização: Summon Night - Swordcraft Story 2 (PT-BR)
**Jogo:** Summon Night: Swordcraft Story 2 (USA) [BSKE]  
**Plataforma:** Game Boy Advance (GBA)  
**Versão:** 2.1 — Diretriz Canônica Unificada (Alinhada a Summon Night 1)  
**Status:** Vital e Mandatório para todos os arquivos e lotes de tradução  
**Engenheiro / Agente:** Antigravity (Google DeepMind)

> Este protocolo herda integralmente as normas do [Protocolo Mestre de Tradução](../../protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md) e consolida a unificação terminológica, conceitual e metodológica entre *Summon Night: Swordcraft Story* (SN1) e *Summon Night: Swordcraft Story 2* (SN2).

---

## 🎯 1. Filosofia de Localização: Eliminação do Inglês e Adaptação Cultural

A tradução deste projeto é um processo de **localização completa, cultural e imersiva**. Todo o universo do jogo é adaptado para o português brasileiro, garantindo a mesma atmosfera artesanal, cômica e heroica concebida pela Flight-Plan/Banpresto:

1. **Eliminação Integral do Inglês:** 100% dos diálogos, menus, comandos de combate, tutoriais, itens, armas, magias, técnicas e bestiário são traduzidos e localizados para PT-BR.
2. **Exceção Estrita: Apenas Nomes Próprios Puros:** Permanecem em seu formato original apenas nomes próprios de pessoas, feras guardiãs, entidades mitológicas e dimensões fantásticas. Nomes compostos, descritivos ou cargos/títulos são obrigatoriamente traduzidos.
3. **Harmonia com o Hardware do GBA:** Respeito absoluto aos limites de pixels e à métrica de 36 caracteres por linha, com quebra manual estrita via `<br>`.

---

## 📊 2. Estudo Comparativo de Métricas: SN1 vs SN2

A transição de ferramentas e métricas entre *Summon Night 1* e *Summon Night 2* revelou um aumento expressivo no volume narrativo e na complexidade das estruturas de dados na ROM:

| Dimensão / Parâmetro | Summon Night 1 (SN1) | Summon Night 2 (SN2) | Impacto Técnico & Diretriz PT-BR |
| :--- | :---: | :---: | :--- |
| **Volume de Diálogos** | ~35.000 linhas | **45.318 linhas** | Aumento de ~30% em densidade dramática e interações de NPCs. |
| **Scripts de Evento/Cena** | 100 scripts (Arch 0/1) | **2.544 scripts** (Arch 2) | 122 scripts compilados na introdução; tabela de alocação de 16-bytes. |
| **Limite por Linha de Diálogo**| 36 caracteres | **36 caracteres** | **Zona Segura:** 1-32 chars \| **Atenção:** 33-35 chars \| **Crítico:** 36+ chars. |
| **Separador de Linhas** | `<br>` | `<br>` | Quebra manual estrita entre as linhas da mesma caixa de diálogo. |
| **Tags de Variáveis de Engine** | `{PLAYER}`, `{PARTNER}`, `{SIBLING}`, `{MASTER}`, `{VAR_2}` | `{PLAYER}`, `{PARTNER}`, `{SIBLING}`, `{MASTER}`, `{VAR_2}`, `{VAR_4}` | Intocáveis pela tradução. Construir sintaxe neutra ao redor. |
| **Armas no Catálogo** | 130 armas | **213 armas** | 140 espadas/machados/lanças + 73 soqueiras/brocas (Stride 132 bytes). |
| **Itens e Materiais** | 120 itens | **156 itens** | Consumíveis, minérios, catalisadores e chave (Stride 132 bytes). |
| **Magias e Técnicas Especiais**| 32 magias | **95 técnicas** | 40 magias (Stride 112 bytes) + 25 combos + 30 efeitos especiais (Stride 74 bytes). |
| **Bestiário (Monstros/Chefes)**| 88 monstros | **114 monstros** | Stride 184 bytes; nomes e descrições de até 4 linhas 100% traduzidos. |
| **Tamanho da ROM Original** | 8 MB | **16 MB** | ROM expandida; ponteiros longos na VM PSI3 e alocação de texto livre. |

---

## 🏛️ 3. Mapeamento Terminológico Unificado (SN1 ➔ SN2)

Conforme estabelecido no primeiro jogo, os termos do universo de *Summon Night* seguem a estratégia de ciclo de vida (apresentação completa no lore/solenidade e uso adaptado conciso nos diálogos e menus):

### 3.1. Termos Centrais do Lore e Classes

| Termo Original (EN-US) | 1ª Apresentação (Lore / Solene) | Uso Comum nos Diálogos | Uso em Menus / UI | Definição no Universo |
| :--- | :--- | :--- | :--- | :--- |
| **Craftlord** | **Lorde da Forja** *(ou Mestre-Ferreiro)* | **Lorde** / **Mestre** | **Lorde** | Mestres ferreiros supremos que regem os forjadores. |
| **Craftknight** | **Cavaleiro-Ferreiro** *(ou Forjador)* | **Ferreiro** / **Forjador** | **Forjador** | Guerreiros-artesãos que forjam e empunham suas próprias armas. |
| **Craftknight Rank** | **Grau de Forjador** | **Rank de Forjador** | **Rank** / **Grau** | Classificação oficial da guilda e oficinas de forja. |
| **Guardian Beast** | **Fera Guardiã** | **Guardião** / **Parceiro** | **Guardião** | Entidade invocada sagrada ligada à alma do forjador. |
| **Summon Beast / Creature** | **Criatura Invocada** | **Invocação** / **Criatura** | **Invocação** | Seres de outras dimensões convocados por magia. |
| **Stray Summon ("Stray")** | **Invocação Errante** | **Errante** | **Errante** | Invocação sem mestre que vaga pelas ruínas e florestas. |
| **Mystic Ore** | **Minério Místico** | **Minério Místico** | **Min. Místico** | Matéria-prima condensada com essência mágica. |
| **Summonite** | **Pedra de Invocação (Summonite)** | **Summonite** | **Summonite** | Pedra mística utilizada na invocação da Fera Guardiã. |
| **Daemon Gem** | **Gema Demônio** / **Gema Demoníaca** | **Gema Demônio** | **Gema Demônio** | Relíquia ancestral selada com a essência de Goura. |
| **Red Daemon Gem** | **Gema Demônio Escarlate** | **Gema Vermelha** | **Gema Verm.** | A gema protetora herdada pelos protagonistas. |
| **Daemon Edge** | **Lâmina Demônio** | **Espada Demoníaca** | **Lâm. Demônio** | A lendária lâmina que mantém o selo primordial de Goura. |
| **Transhift** | **Transmutação** / **Metamorfose** | **Transhift** | **Transhift** | A transformação de combate ativada pela Gema Demônio. |
| **Shapestones** | **Pedras de Forja** / **Matrizes** | **Pedras de Forja** | **Pedra Forja** | Matrizes usadas na forja de novas categorias de armas. |
| **Durability** | **Durabilidade** | **Durabilidade** | **DUR** | Integridade física da lâmina antes de se quebrar. |
| **Upgrades** | **Aprimoramentos** | **Melhorias** | **Melhoria** | Fortalecimento de atributos e técnicas na bancada. |
| **Special Attack** | **Ataque Especial** | **Ataque Especial** | **Ataque Esp.** | Golpes e sequências especiais de armas. |
| **Special Effect** | **Efeito Especial** | **Efeito Especial** | **Efeito Esp.** | Propriedades elementais ou drenos na lâmina. |
| **Boam** | **Boam** | **Boam** | **Boam** | A moeda oficial do universo de Summon Night. |

---

### 3.2. Categorias de Armas e Forja (100% Traduzidas)

| Categoria Original | Tradução em Menus / Equipamento | Tradução em Diálogos | Exemplo de Arma Adaptada |
| :--- | :---: | :--- | :--- |
| **`Sword Type`** | **`Espada`** | **`Técnica com Espada`** | *Amateur Knife* $\rightarrow$ **Faca de Aprendiz**<br>*Grand Saber* $\rightarrow$ **Grão-Sabre** |
| **`Axe Type`** | **`Machado`** | **`Técnica com Machado`** | *Battle Axe* $\rightarrow$ **Machado de Batalha**<br>*Heavy Axe* $\rightarrow$ **Machado Pesado** |
| **`Spear Type`** | **`Lança`** | **`Técnica com Lança`** | *Light Spear* $\rightarrow$ **Lança Leve**<br>*Long Lance* $\rightarrow$ **Lança Longa** |
| **`Knuckle Type`** | **`Soqueira`** | **`Técnica com Soqueira`** | *Iron Knuckle* $\rightarrow$ **Soqueira de Ferro**<br>*Spike Glove* $\rightarrow$ **Luva de Espinhos** |
| **`Drill Type`** | **`Broca`** | **`Técnica com Broca`** | *Spiral Drill* $\rightarrow$ **Broca Espiral**<br>*Turbo Auger* $\rightarrow$ **Broca Turbo** |

---

### 3.3. Itens, Acessórios e Minérios (100% Traduzidos)

| Item Original (EN-US) | Tradução Oficial PT-BR | Descrição Localizada PT-BR |
| :--- | :--- | :--- |
| **Healing Herb** | **Erva Medicinal** | Erva silvestre que restaura uma porção de HP. |
| **Potion** | **Poção** | Medicamento líquido para recuperação básica. |
| **High Potion** | **Superpoção** | Remédio refinado com alto poder de cura. |
| **Antidote Ore** | **Minério Antídoto** | Minério com propriedades purificadoras de toxinas. |
| **Iron Ore** | **Minério de Ferro** | Metal comum básico para forja de armas iniciais. |
| **Hero's Badge** | **Brasão do Herói** | Amuleto honorário que fortalece a defesa do portador. |

---

### 3.4. Bestiário e Monstros (100% Traduzidos)

Nenhum monstro deve manter grafia ou termos em inglês. Monstros com nomes truncados na versão americana da ROM devem ser restaurados para termos nobres em português:

| Nome na ROM (EN-US) | Tradução Oficial PT-BR | Descrição Traduzida PT-BR |
| :--- | :--- | :--- |
| **`nabeetle`** | **Besouro-Pote** | Besouro popular antigamente criado para disputas esportivas. |
| **`und`** (Hound) | **Lobo Feroz** | Lobo voraz cujas presas são capazes de perfurar aço. |
| **`lly Slime`** (Jelly Slime) | **Gosma Geleia** | Criatura misteriosa de consistência pegajosa. |
| **`Runnerhead`** | **Cabeça-Corredora** | Atenção! Criatura extremamente ágil e perigosa. |
| **`Mud Boxer`** | **Lutador de Lama** | Criatura cujo corpo é formado inteiramente por lama e lodo. |
| **`Evil Spirit`** | **Espírito Maligno** | Assombração atraída por tempestades e raios. |
| **`Red Gremlin`** | **Gremlin Vermelho** | Conhecido como o Garoto Demônio, mesmo quando adulto. |
| **`Iron Giant`** | **Gigante de Ferro** | Construto metálico colossal de tremendo poder de impacto. |

---

### 3.5. Cidades, Regiões e Masmorras (Nomes Compostos Traduzidos)

| Nome Original | Tradução Oficial Adotada (PT-BR) | Tipo de Local |
| :--- | :--- | :--- |
| **Cliff Village** | **Vila do Penhasco** | Povoado natal de Edgar e Aera no topo do precipício. |
| **Entry Woods** | **Bosque da Entrada** | Mata que cerca os limites de acesso à vila. |
| **Goura's Gate** | **Portão de Goura** | O santuário proibido onde o demônio Goura foi selado. |
| **Subterranean Canal** | **Canal Subterrâneo** | Galeria aquática abaixo das ruínas ancestrais. |
| **Fire Fortress** | **Fortaleza de Fogo** | Fortaleza vulcânica habitada por espíritos ígneos. |
| **Ruined Factory** | **Fábrica em Ruínas** | Instalação mecânica arruinada ligada ao mundo de Loreilal. |
| **Daemon Vault** | **Câmara do Demônio** | O coração profundo onde dorme o poder de Goura. |
| **Living Quarters** | **Aposentos Residenciais** | Ala residencial dos antigos guardiões do complexo. |
| **Central Plaza** | **Praça Central** | Ponto de encontro e comércio de Cliff Village. |

---

### 3.6. Nomes Próprios Mantidos Intactos

Permanecem estritamente originais:
* **Protagonistas:** `Edgar`, `Aera`.
* **Mestre e Aliados:** `Blaire`, `Orin`, `Ryouga`, `Lynn`, `Gabriel`, `Nina`, `Tatiana`.
* **Rivais e Mestres:** `Borgrim`, `GUNVALD`, `Toris`, `Magna`.
* **Feras Guardiãs (*Guardian Beasts*):** `EXeLD`, `Dinah`, `Arno`, `Loki`.
* **Mundos e Dimensões Canônicas:** `Lyndbaum`, `Silturn`, `Sapureth`, `Loreilal`, `Maetropa`.
* **Entidade Ancestral Primordial:** `Goura`.

---

## ⚡ 4. Pilares Técnicos de Engenharia e Métricas de Tela

### 4.1. Zonas de Segurança e Limites de Linha (GBA)
Conforme auditoria em `estudo-de-metricas-e-caracteres.md`:
* **Hard Limit:** **36 caracteres por linha** (Teto físico absoluto antes do clipping na moldura).
* **Zona Segura:** **1 a 32 caracteres** (Ideal para leitura fluida e confortável).
* **Zona de Atenção:** **33 a 35 caracteres** (Permitido apenas se contiver glifos finos como `i`, `l`, `t`, pontuação).
* **Quebra de Linha:** Separador obrigatório `<br>` entre as linhas de uma mesma caixa de fala.
* **Orfandade Proibida:** Nunca isolar monossílabos (`o`, `a`, `de`, `em`) no final da linha.

### 4.2. Proteção Rígida de Tags e Variáveis da VM PSI3
As variáveis dinâmicas injetadas pelo código ASM são intocáveis:
- `{PLAYER}`: Nome do protagonista (Edgar ou Aera).
- `{PARTNER}`: Nome da Fera Guardiã parceira.
- `{SIBLING}`: Tratamento do irmão/irmã adotivo(a).
- `{MASTER}`: Nome do mestre ou invocador antigo.
- `{VAR_2}` / `{VAR_4}`: Nomes de técnicas e magias aprendidas dinamicamente.

### 4.3. Tabela Canônica de Abreviações para Menus e Itens

| Conceito / Termo | Abreviação Oficial | Exemplo Prático |
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

---

## 📌 5. Checklist Rápido de Liberação de Lote

Antes de aprovar qualquer linha ou lote traduzido:
- [ ] Todas as linhas respeitam a métrica máxima de **32 a 35 caracteres**?
- [ ] O texto soa natural para um falante nativo do Brasil?
- [ ] A concordância de gênero neutro foi mantida em falas compartilhadas?
- [ ] Todo texto de sistema, armas, itens, monstros e menus em inglês foi eliminado?
- [ ] Foram mantidos no original estritamente os nomes próprios de pessoas e mundos?
- [ ] As tags dinâmicas (`{PLAYER}`, `{PARTNER}`, etc.) continuam 100% intactas?
- [ ] Nenhum diálogo contém palavras abreviadas?
