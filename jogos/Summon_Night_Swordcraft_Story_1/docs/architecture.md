# Arquitetura e Mapa de Memória — Summon Night: Swordcraft Story (GBA)

Este documento centraliza o mapeamento técnico da ROM de **Summon Night: Swordcraft Story (USA)** (`AB4E`), incluindo especificações de hardware do Game Boy Advance (ARM7TDMI), layout de memória extraído pela inspeção real da ROM e convenções para a descompilação e localização PT-BR sem limites de memória.

---

## 1. Identificação Oficial da ROM Analisada

| Propriedade | Valor Extraído |
| :--- | :--- |
| **Arquivo Base** | `Summon Night - Swordcraft Story (USA).gba` |
| **Tamanho Total** | `8,388,608` bytes (**8.0 MB** / 64 Mbit) |
| **CRC32 / MD5 / SHA-1** | `3EA860C2` / `3fa7e703d48e070d9c762c2404e91a566a50166e` |
| **Game Title (0xA0)** | `SUMMONIGHSCS` |
| **Game Code (0xAC)** | `AB4E` (USA / English) |
| **Maker Code (0xB0)** | `EB` (Atlus / Banpresto / Flight-Plan) |
| **Entry Point (0x00)** | `0xEA00002E` $\rightarrow$ `B 0x080000C0` (ARM Branch para offset `0x000000C0`) |
| **Header Checksum (0xBD)**| `0x2E` (**Válido**) |

---

## 2. Mapa de Memória da ROM (`0x08000000` – `0x087FFFFF`)

Com base na análise de entropia, contagem de literal pools/ponteiros (`0x08XXXXXX`) e densidade ASCII realizada pelo [rom_inspector.py](file:///f:/USER/Documents/Antigravity/Tradu%C3%A7%C3%A3o%20GBA/tools/rom_inspector.py) (salva em [rom_map.json](file:///f:/USER/Documents/Antigravity/Tradu%C3%A7%C3%A3o%20GBA/extracted/rom_map.json)):

| Faixa de Endereço (ROM) | File Offset | Bancos (64 KB) | Tipo / Conteúdo Identificado |
| :--- | :--- | :--- | :--- |
| `0x08000000` – `0x080000BF` | `0x000000` – `0x0000BF` | `#000` | **GBA ROM Header** (Entry Point + Nintendo Logo + Game Code `AB4E`) |
| `0x080000C0` – `0x0805FFFF` | `0x0000C0` – `0x05FFFF` | `#000` – `#005` | **Código Executável Principal (ARM/THUMB)** (~384 KB, altíssima densidade de ponteiros `0x08XXXXXX` em literal pools: 735 a 1164 por banco) |
| `0x08060000` – `0x0806FFFF` | `0x060000` – `0x06FFFF` | `#006` | **Tabelas de Dados, Strings Fixas de Sistema/Menu e Scripts Iniciais** (Alta densidade ASCII: `41%`) |
| `0x08070000` – `0x08760C20` | `0x070000` – `0x760C20` | `#007` – `#118` | **Assets, Gráficos 4BPP/8BPP, Bancos de Diálogo/Eventos Comprimidos e Áudio** |
| `0x08760C21` – `0x087FFFFF` | `0x760C21` – `0x7FFFFF` | `#118` – `#127` | **Espaço Livre Contínuo (`0x00` Padding)**: **636.97 KB** (`652,255` bytes livres, `7.78%` da ROM) |

---

## 3. Estratégia de Localização Sem Limite de Memória

1. **Espaço Livre Nativo (636.97 KB):**
   - A ROM de 8 MB já possui quase **637 KB de espaço livre contínuo** entre `0x08760C21` e `0x087FFFFF` preenchido com `0x00`. Isso é suficiente para realocar todos os bancos de diálogo em PT-BR com folga sem sequer aumentar o tamanho do arquivo.
2. **Expansão Opcional para 16 MB / 32 MB (`0x08800000` – `0x09FFFFFF`):**
   - Como o barramento do GBA endereça até 32 MB linearmente no Wait State 0 (`0x08000000`–`0x09FFFFFF`), podemos anexar **+8 MB ou +24 MB** ao final da ROM caso desejemos incluir gráficos descomprimidos, fontes VWF expandidas ou bancos extras de script.

---

## 4. Mapa de Memória de Hardware do GBA (ARM7TDMI)

| Região | Endereço Inicial | Endereço Final | Tamanho | Largura de Barramento | Notas |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **BIOS (System ROM)** | `0x00000000` | `0x00003FFF` | 16 KB | 32-bit | Funções SWI (`SoftReset`, `LZ77UnCompWram`, `VBlankIntrWait`) |
| **EWRAM (On-board WRAM)** | `0x02000000` | `0x0203FFFF` | 256 KB | 16-bit | Heap principal, buffers de script descomprimidos, estado global |
| **IWRAM (On-chip WRAM)** | `0x03000000` | `0x03007FFF` | 32 KB | 32-bit | Rotinas críticas em ARM, pilha (`SP_irq`, `SP_svc`, `SP_usr`), BSS rápido |
| **I/O Registers** | `0x04000000` | `0x040003FE` | 1 KB | 16/32-bit | Controle de LCD (`DISPCNT`), DMA0-3, Timers, Sound, Key Input |
| **Palette RAM** | `0x05000000` | `0x050003FF` | 1 KB | 16-bit | 256 cores BG (`0x05000000`) + 256 cores OBJ (`0x05000200`) |
| **VRAM (Video RAM)** | `0x06000000` | `0x06017FFF` | 96 KB | 16-bit | Tiles de fonte/diálogo, tilemaps de caixa de texto e sprites |
| **OAM (Object Attributes)** | `0x07000000` | `0x070003FF` | 1 KB | 32-bit | Até 128 entradas de hardware sprites |
| **Game Pak ROM (Wait State 0)** | `0x08000000` | `0x09FFFFFF` | Até 32 MB | 16-bit | Código THUMB/ARM, bancos de texto, gráficos e música |
| **Game Pak SRAM / Flash** | `0x0E000000` | `0x0E00FFFF` | 64 KB | 8-bit | Save data |
