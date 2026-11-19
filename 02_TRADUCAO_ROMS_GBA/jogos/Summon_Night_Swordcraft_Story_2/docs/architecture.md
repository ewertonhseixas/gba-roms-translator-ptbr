# 🏛️ Arquitetura Técnica: Summon Night - Swordcraft Story 2 (GBA)

Este documento descreve a estrutura interna de memória, ponteiros, sistema de arquivos em contêineres e motor de script da ROM de **Summon Night: Swordcraft Story 2** (*Banpresto / Flight-Plan, 2006*).

---

## 📊 Metadados da ROM Original

| Parâmetro | Valor | Detalhes |
| :--- | :--- | :--- |
| **Nome do Arquivo** | `Summon Night - Swordcraft Story 2 (USA).gba` | Versão oficial americana |
| **Título Interno** | `SWORDCRAFT2` | Offset `0x00A0`..`0x00AB` |
| **Game Code** | `BSKE` | Offset `0x00AC`..`0x00AF` |
| **Maker Code** | `EB` (Banpresto) | Offset `0x00B0`..`0x00B1` |
| **Tamanho da ROM** | `16.777.216 bytes` (16,00 MB) | Dobro da memória do primeiro jogo |
| **Base de Memória ROM** | `0x08000000` | Barramento ROM0 do GBA |

---

## 🗃️ Sistema de Arquivos (Master Archives)

A engine da Flight-Plan carrega dados através de uma tabela mestra de 5 arquivos raiz registrada na rotina `Archive_Init` em `0x08003DA8` (ponteiros armazenados em RAM `0x03002FF0`):

| Archive # | Endereço ROM | Offset em Disco | Qtd. Entradas | Conteúdo Principal |
| :---: | :---: | :---: | :---: | :--- |
| **Archive 0** | `0x085015CC` | `0x005015CC` | 35 sub-contêineres | Mapas, Tilesets, Cenários e Sub-arquivos de eventos |
| **Archive 3** | `0x089436FC` | `0x009436FC` | 27 arquivos | Fontes (`BIT\0` em `0x08944D3C`), Gráficos de Interface (CG4) e Telas de Sistema |
| **Archive 2** | `0x08ABA81C` | `0x00ABA81C` | **2.551 arquivos** | **Engine de Diálogos e Eventos PSI3 (972 scripts comprimidos em LZ77)** |
| **Archive 1** | `0x08C7F5FC` | `0x00C7F5FC` | 5 sub-contêineres | Gráficos de Batalha e Sprites de monstros |
| **Archive 4** | `0x08FB6DEC` | `0x00FB6DEC` | 81 arquivos | Áudios, HUD e tabelas finais |

*(Do fim do Archive 4 em `0x08FCC05C` até `0x09000000` existem 212 KB de espaço livre contínuo para injeções e expansões).*

---

## 📜 Motor de Scripts PSI3 & Textos

1. **Formato do Script:** Bytecode nativo do motor proprietário `PSI3` (iniciado pelo cabeçalho mágico de 4 bytes `PSI3`).
2. **Compressão:** Os scripts no Archive 2 são comprimidos utilizando a compressão padrão **GBA BIOS LZ77 (tipo `0x10`)**. Ao descomprimir, revelam os fluxos de instruções e strings do jogo.
3. **Codificação dos Textos:** Codificação de 16 bits **Shift-JIS Full-Width (Zen-kaku)**:
   - Caracteres latinos mapeados em `0x8260..0x8279` (Maiúsculas) e `0x8281..0x829A` (Minúsculas).
   - Pontuações e símbolos em `0x8140..0x81F4`.
   - Variáveis dinâmicas da engine: `{PLAYER}`, `{PARTNER}`, `{SIBLING}`, `{MASTER}`.
4. **Fonte:** Fonte de 1bpp monocromática (12x12 pixels) localizada em `0x08944D3C` (Archive 3, arquivo 2) com suporte a sombras em tempo real aplicadas pela rotina gráfica do GBA.

---

## ⚙️ Tabelas de Instruções da Máquina Virtual PSI3

O despachador de opcodes da VM reside em `0x08026AA6` e redireciona os comandos para 5 blocos de rotinas principais:

- **Tabela 0 (0x0000):** `0x084CA9D0` (saltos, chamadas de rotina e expressões lógicas)
- **Tabela 1 (0x0100):** `0x084CAA10` (gatilhos de mapa e atores)
- **Tabela 2 (0x0200):** `0x084CAA6C` (diálogos, escolhas, variáveis e caixas de texto)
- **Tabela 3 (0x0300):** `0x084CABAC` (animações, efeitos visuais e threads)
- **Tabela 4 (0x0400):** `0x084CAE30` (funções auxiliares e extensões)
