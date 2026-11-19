# 🔍 Relatório de Auditoria e Fingerprint da ROM
**Arquivo Analisado:** `Summon Night - Swordcraft Story (USA).gba`  
**Plataforma Detectada:** Game Boy Advance (GBA)  
**Tamanho do Arquivo:** 8,388,608 bytes (8.00 MB)  
**Validação de Cabeçalho GBA:** ✅ Válido  

---

## 🏷️ 1. Metadados Oficiais da ROM

| Campo do Cabeçalho | Valor Identificado | Significado |
| :--- | :--- | :--- |
| **Título do Jogo** | `SUMMONIGHSCS` | Nome gravado no registro interno do cartucho |
| **Game Code (Serial)** | `AB4E` | Código de 4 letras da Nintendo |
| **Maker Code** | `EB` | ID da publicadora/desenvolvedora |
| **Versão de Software** | `v1.0` | Revisão oficial do cartucho |
| **Complement Check** | `0x2e` | ✅ Checksum íntegro |

---

## 🎬 2. Auditoria de Vídeos e FMVs

> ✅ **Nenhum codec de vídeo dedicado detectado.** A ROM utiliza gráficos nativos de sprites e tilesets para animações e cinemáticas.

---

## 📦 3. Compressões de Dados e Gráficos da BIOS

| Tipo de Compressão | Blocos Estimados na ROM | Observações |
| :--- | :---: | :--- |
| **BIOS LZ77 (`0x10`)** | `8162` | Padrão mais comum para tilesets, sprites e mapas |
| **Huffman (`0x20`/`0x30`)** | `41690` | Usado ocasionalmente para fontes e dados densos |
| **RLE (`0x40`)** | `16976` | Compressão linear simples de repetição |

---

## 🎯 4. Tabelas de Ponteiros Identificadas (Amostra das Maiores)

Foram localizadas **99 tabelas sequenciais de ponteiros de 32-bit** na ROM. As 10 mais extensas:

| Offset Inicial | Offset Final | Qtd. Ponteiros | Primeiro Destino | Último Destino |
| :--- | :--- | :---: | :--- | :--- |
| `0x001D84F0` | `0x001DAE30` | **2640** | `0x08070F50` | `0x08070F40` |
| `0x00033974` | `0x00033CAC` | **206** | `0x08033978` | `0x08035640` |
| `0x0004E3F0` | `0x0004E5F4` | **129** | `0x0804E3F4` | `0x0804EEFC` |
| `0x00051FD8` | `0x000521DC` | **129** | `0x08051FDC` | `0x080528D8` |
| `0x001DD8B0` | `0x001DDAA4` | **125** | `0x08071398` | `0x08071338` |
| `0x0002C5E0` | `0x0002C7C4` | **121** | `0x0802C5E4` | `0x0802C7D8` |
| `0x00046818` | `0x000469F4` | **119** | `0x0804681C` | `0x0804772C` |
| `0x0005D828` | `0x0005DA04` | **119** | `0x0805D82C` | `0x0805DC4C` |
| `0x00058B68` | `0x00058D38` | **116** | `0x08058B6C` | `0x0805A370` |
| `0x0003E088` | `0x0003E22C` | **105** | `0x0803E08C` | `0x0803E7C6` |
