# 🛠️ Ferramentas de Extração, Engenharia Reversa e Compilação (ROM Hacking GBA)

Este diretório contém todo o conjunto de ferramentas desenvolvido para engenharia reversa, extração, edição de textos, injeção gráfica, validação interativa e compilação automatizada da ROM.

Todas as ferramentas foram mantidas modulares e documentadas para que possam ser **reutilizadas diretamente em outros projetos de tradução e ROM hacking de Game Boy Advance (GBA)**, especialmente outros títulos da franquia (*Summon Night: Swordcraft Story 2*) e jogos com arquiteturas semelhantes desenvolvidos pela Flight-Plan / Banpresto.

---

## 📋 Sumário das Ferramentas

| Ferramenta | Categoria | Finalidade Principal |
| :--- | :--- | :--- |
| [`build_ptbr_rom.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/build_ptbr_rom.py) | **Compilador Central** | Pipeline mestre: recompila diálogos PSI3, injeta fontes, tabelas estáticas, aplica patches na engine e gera patch IPS. |
| [`translation_validator_app.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/translation_validator_app.py) | **Interface Web / QA** | Servidor local de validação de textos, contagem de caracteres por linha e teste em tempo real na ROM. |
| [`validator_ui.html`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/validator_ui.html) | **Interface Web / QA** | Interface gráfica moderna com preview pixel art de caixas de diálogo do GBA. |
| [`archive_extractor.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/archive_extractor.py) | **Formatos de Arquivo** | Extrai contêineres e sub-arquivos binários da ROM (suporta LZ77 padrão GBA tipo `0x10` e cabeçalhos proprietários). |
| [`psi3_rebuilder.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/psi3_rebuilder.py) | **Engine de Script** | Desmonta, recalibra ponteiros internos e recompila bytecode de diálogos e eventos do motor PSI3. |
| [`psi3_opcode_scanner.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/psi3_opcode_scanner.py) | **Engine de Script** | Mapeia todos os opcodes de controle do motor de eventos e branches condicionais. |
| [`psi3_inspector.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/psi3_inspector.py) | **Engine de Script** | Inspeção detalhada de cabeçalhos, seções de texto e metadados de scripts PSI3 individuais. |
| [`font_ptbr_injector.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/font_ptbr_injector.py) | **Tipografia / Gráficos** | Injeta glifos acentuados PT-BR (`á`, `é`, `í`, `ã`, `ç`, etc.) nos tiles de fonte e aplica NOP na engine. |
| [`menu_graphics_ptbr.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/menu_graphics_ptbr.py) | **Gráficos / UI** | Manipulação de tiles 4bpp/8bpp e compressão LZ77 para gráficos de menus, telas de título e HUD. |
| [`extract_all_graphics.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/extract_all_graphics.py) | **Gráficos** | Extrator em lote de tiles e paletas gráficas indexadas para visualização em PNG. |
| [`extract_game_data.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/extract_game_data.py) | **Tabelas de Dados** | Extração estruturada de catálogos: armas, itens, materiais, técnicas e bestiário com descrições. |
| [`verify_ptbr_rom_and_data.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/verify_ptbr_rom_and_data.py) | **Auditoria / QA** | Auditoria automatizada: valida integridade da ROM, ponteiros de menus, patches da engine e sincronização 100% com o JSON de dados. |
| [`extract_audio.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/extract_audio.py) | **Áudio** | Identificação e extração de tabelas sonoras, amostras PCM e sequenciamento de música do GBA. |
| [`text_locator.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/text_locator.py) | **Localizador de Texto** | Varredura de strings na ROM por codificações ASCII, Shift-JIS ou tabelas personalizadas (.tbl). |
| [`sjis_script_dumper.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/sjis_script_dumper.py) | **Dumper de Texto** | Dump de scripts e diálogos em formato Shift-JIS com tags de controle preservadas. |
| [`batch_dialogue_generator.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/batch_dialogue_generator.py) | **Automação** | Gerador e sincronizador de tabelas Markdown (`ARQUIVOS md/`) a partir de pacotes JSON de extração. |
| [`xref_analyzer.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/xref_analyzer.py) | **Engenharia Reversa** | Localizador de referências cruzadas (ponteiros de 32-bit `0x08XXXXXX`) apontando para textos e dados na ROM. |
| [`disasm_boot.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/disasm_boot.py) | **Engenharia Reversa** | Desmontador de rotinas ARM/Thumb da inicialização do jogo para localizar rotinas de descompressão. |

---

## 🚀 Como Executar as Principais Ferramentas

### 1. Compilar a ROM e Gerar o Patch IPS
Execute no terminal ou dê um duplo-clique no arquivo `.bat`:
```cmd
python tools/build_ptbr_rom.py
```
* **Entradas:** `rom/Summon Night - Swordcraft Story (USA).gba`, arquivos em `ARQUIVOS md/`.
* **Saídas:**
  - `rom/Summon Night - Swordcraft Story (PT-BR).gba` (ROM de 8,00 MB validada).
  - `releases/Summon Night - Swordcraft Story (PT-BR) vX.X.ips` (Patch IPS pronto para distribuição).

### 2. Abrir o Validador Visual de Tradução (App Web)
```cmd
python tools/translation_validator_app.py
```
* Abre automaticamente em `http://localhost:8080`.
* Permite pesquisar qualquer script, editar falas, testar quebras de linha (`<br>`) e recompilar instantaneamente.

### 3. Extrair Contêineres de Dados (Archives)
```cmd
python tools/archive_extractor.py
```
* Extrai os sub-arquivos comprimidos e descomprimidos do jogo para análise individual.

---

## 🔄 Reutilização em Outras ROMs

Ao adaptar este toolkit para outro jogo de GBA:
1. **Ponteiros de Memória (ROM Offset):** No GBA, os ponteiros apontam para a faixa `0x08000000`–`0x09FFFFFF`. Utilize o [`xref_analyzer.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/xref_analyzer.py) para mapear onde a nova ROM armazena suas tabelas de ponteiros.
2. **Compressão LZ77:** A função de descompressão LZ77 padrão do BIOS do GBA (`SWI 0x11` / `0x12`) implementada em [`archive_extractor.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/archive_extractor.py) é idêntica em quase todos os jogos de GBA comerciais.
3. **Injeção de Caracteres Especiais:** O algoritmo em [`font_ptbr_injector.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/font_ptbr_injector.py) substitui tiles de caracteres não utilizados (ou amplia a tabela 1-byte) para adicionar `Á, É, Í, Ó, Ú, Ã, Õ, Ç, etc.` sem quebrar a proporção do jogo.
4. **Gerador de Patches IPS:** A rotina `create_ips_patch()` presente em [`build_ptbr_rom.py`](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/tools/build_ptbr_rom.py) é 100% agnóstica a jogos e pode gerar patches para qualquer ROM de até 16 MB.
