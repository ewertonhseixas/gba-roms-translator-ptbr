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

## 2. Termos Centrais do Universo e Lore (*Glossário Base*)

| Termo Original (EN-US / JP) | Tradução Sugerida (Opção A) | Alternativa (Opção B) | Contexto e Definição no Jogo | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Exemplo: Kingdom** | **Reino** | **Império** | Designação geopolítica do continente principal. | ⏳ Pendente |
| **Exemplo: Mana Crystal** | **Cristal de Mana** | **Cristal de Mana** | Fonte primordial de magia utilizada por conjuradores. | ⏳ Pendente |
| **Exemplo: Guild Master** | **Mestre da Guilda** | **Líder da Guilda** | Título hierárquico concedido ao regente da guilda local. | ⏳ Pendente |

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
