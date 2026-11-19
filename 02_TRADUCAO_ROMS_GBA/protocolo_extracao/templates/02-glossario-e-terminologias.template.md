# 02 — Glossário Oficial, Personagens, Locais e Variáveis de Sistema
**Jogo:** [NOME DO JOGO]  
**Plataforma:** GBA / [CONSOLA]  
**Status do Arquivo:** Em Construção  

Este documento reúne todos os **nomes próprios, terminologias centrais do universo, títulos de lore, variáveis de controle de engine e nomes de cidades/mapas**. Serve como autoridade máxima de consulta para garantir que a terminologia seja consistente em 100% dos diálogos.

---

## 1. Variáveis de Controle e Tags da Engine de Texto

Variáveis de substituição dinâmica em tempo de execução (ex: nome do jogador, parceiro, itens recebidos, números):

| Tag no Script | Código Hex / Bytecode | Valor Padrão (Original) | Tradução / Adaptação Sugerida (PT-BR) | Observações e Comportamento | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `{PLAYER}` | `0x...` | `Hero` | `{PLAYER}` | Nome definido pelo jogador ao iniciar o jogo. | ⏳ Pendente |
| `{PARTNER}` | `0x...` | `Partner` | `{PARTNER}` | Nome do companheiro/parceiro da história. | ⏳ Pendente |
| `{ITEM}` | `0x...` | `Item Name` | `{ITEM}` | Substituído pelo nome do item encontrado ou recebido. | ⏳ Pendente |
| `{NUMBER}` | `0x...` | `Quantity` | `{NUMBER}` | Substituído por quantidade numérica ou quantia de dinheiro. | ⏳ Pendente |
| `{LINE}` | `0x...` | `<br>` | `<br>` | Quebra de linha da caixa de diálogo. | ⏳ Pendente |

---

## 2. Termos Centrais do Universo e Lore (*Glossário Base — Summon Night*)

> **Nota:** Consulte sempre o **[Glossário Global da Franquia Summon Night](../../protocolo_traducao/GLOSSARIO_GLOBAL_SUMMON_NIGHT.md)** para a lista completa de mundos, facções, itens, magias e bestiário compartilhados entre os 13 jogos.

| Termo Original (EN-US / JP) | Tradução Canônica (1ª Aparição / Lore) | Forma Curta (Diálogos / UI) | Contexto e Definição no Jogo | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Craftknight** (*鍛冶師 / クラフトナイト*) | **Cavaleiro Forjador** | **Cavaleiro / Forjador** | Guerreiros-artesãos que forjam e empunham suas próprias armas. | ✅ Canônico |
| **Craftlord** (*鍛冶王 / クラフトロード*) | **Lorde Forjador** | **Lorde** | O mais alto título de maestria entre os Cavaleiros Forjadores. | ✅ Canônico |
| **Summoner** (*召喚師*) | **Invocador(a)** | **Invocador** | Conjurador capaz de realizar rituais e pactos de invocação. | ✅ Canônico |
| **Summon Beast** (*召喚獣*) | **Fera Invocada / Invocação** | **Invocação** | Seres chamados dos mundos paralelos (Silturn, Loreilal, Sapureth, Maetropa). | ✅ Canônico |
| **Guardian Beast** (*護衛獣*) | **Fera Guardiã** | **Guardião / Parceiro** | A criatura invocada ligada por pacto que protege o protagonista. | ✅ Canônico |
| **Summon Stray / Stray** (*野良召喚獣*) | **Invocação Errante** | **Errante** | Invocação sem mestre que vaga livremente pelas masmorras. | ✅ Canônico |
| **Summonite** (*召喚石*) | **Pedra de Invocação** | **Pedra de Invocação** *(UI: Pedra Invoc.)* | Mineral místico usado para invocar criaturas e canalizar magias. | ✅ Canônico |
| **Mystic Ore** (*魔鉱石*) | **Minério Místico** | **Minério Místico** *(UI: Min. Místico)* | Minério que confere atributos mágicos às armas. | ✅ Canônico |

---

## 3. Cidades, Regiões, Mapas e Instalações

| Offset / ID | Nome Original | Nome Sugerido (PT-BR) | Tipo de Local | Status |
| :--- | :--- | :--- | :--- | :---: |
| `0x0001` | `Central Plaza` | `Praça Central` | Ponto de encontro e comércio da capital. | ⏳ Pendente |
| `0x0002` | `Ancient Ruins` | `Ruínas Ancestrais` | Calabouço principal com labirintos e quebra-cabeças. | ⏳ Pendente |
| `0x0003` | `Blacksmith Shop` | `Ferraria` | Estabelecimento onde armas são aprimoradas. | ⏳ Pendente |

---

## 4. Elementos, Magias e Estados de Status

| Nome Original | Tradução Sugerida (PT-BR) | Efeito / Descrição Breve | Status |
| :--- | :--- | :--- | :---: |
| `Fire / Flame` | `Fogo / Chama` | Elemento ígneo, causa dano térmico adicional. | ⏳ Pendente |
| `Poison` | `Veneno` | Estado de status: drena vida a cada turno/passo. | ⏳ Pendente |
| `Paralysis` | `Paralisia` | Estado de status: impede movimentação ou ações. | ⏳ Pendente |
