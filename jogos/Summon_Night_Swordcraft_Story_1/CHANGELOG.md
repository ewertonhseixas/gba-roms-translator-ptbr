# Changelog — Tradução PT-BR: Summon Night - Swordcraft Story (GBA)

Todas as alterações e lançamentos significativos deste projeto serão documentados neste arquivo a partir da **v0.1**.

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
