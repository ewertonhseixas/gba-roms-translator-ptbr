# 🔍 Relatório de Auditoria e Fingerprint da ROM
**Arquivo Analisado:** `Summon Night - Swordcraft Story 2 (USA).gba`  
**Plataforma Detectada:** Game Boy Advance (GBA)  
**Tamanho do Arquivo:** 16,777,216 bytes (16.00 MB)  
**Validação de Cabeçalho GBA:** ✅ Válido  

---

## 🏷️ 1. Metadados Oficiais da ROM

| Campo do Cabeçalho | Valor Identificado | Significado |
| :--- | :--- | :--- |
| **Título do Jogo** | `SWORDCRAFT2` | Nome gravado no registro interno do cartucho |
| **Game Code (Serial)** | `BSKE` | Código de 4 letras da Nintendo |
| **Maker Code** | `EB` | ID da publicadora/desenvolvedora |
| **Versão de Software** | `v1.0` | Revisão oficial do cartucho |
| **Complement Check** | `0x74` | ✅ Checksum íntegro |

---

## 🎬 2. Auditoria de Vídeos e FMVs

> ⚠️ **ATENÇÃO! Fluxo de vídeo ou FMV identificado na ROM!**

| Assinatura | Offset na ROM | Descrição Técnica |
| :---: | :--- | :--- |
| `MOC4` | `0x003DBA7D` | Mobiclip Video Codec v4 (GBA Video / Cutscenes) |

**Diretriz:** Notificar o tradutor para estudo de viabilidade de legendagem (hardsub vs softsub overlay).

---

## 📦 3. Compressões de Dados e Gráficos da BIOS

| Tipo de Compressão | Blocos Estimados na ROM | Observações |
| :--- | :---: | :--- |
| **BIOS LZ77 (`0x10`)** | `12698` | Padrão mais comum para tilesets, sprites e mapas |
| **Huffman (`0x20`/`0x30`)** | `84585` | Usado ocasionalmente para fontes e dados densos |
| **RLE (`0x40`)** | `36556` | Compressão linear simples de repetição |

---

## 🎯 4. Tabelas de Ponteiros Identificadas (Amostra das Maiores)

Foram localizadas **106 tabelas sequenciais de ponteiros de 32-bit** na ROM. As 10 mais extensas:

| Offset Inicial | Offset Final | Qtd. Ponteiros | Primeiro Destino | Último Destino |
| :--- | :--- | :---: | :--- | :--- |
| `0x00062074` | `0x0006284C` | **502** | `0x08062078` | `0x080635BA` |
| `0x004E0574` | `0x004E088C` | **198** | `0x08091728` | `0x0809083C` |
| `0x0008A354` | `0x0008A510` | **111** | `0x0808A358` | `0x0808A7FC` |
| `0x000477A0` | `0x00047958` | **110** | `0x080477A4` | `0x08047DEC` |
| `0x0002E4D4` | `0x0002E688` | **109** | `0x0802E4D8` | `0x0802EC28` |
| `0x0004CED4` | `0x0004D06C` | **102** | `0x0804CED8` | `0x0804D1B0` |
| `0x00008CB0` | `0x00008E38` | **98** | `0x08008CB4` | `0x080095E8` |
| `0x00024DF0` | `0x00024F68` | **94** | `0x08024DF4` | `0x08025308` |
| `0x004CABAC` | `0x004CAD04` | **86** | `0x08011C85` | `0x08070541` |
| `0x00059BFC` | `0x00059D48` | **83** | `0x08059C00` | `0x0805A414` |
