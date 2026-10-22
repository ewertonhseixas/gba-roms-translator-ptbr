# Contexto do Projeto: Engenharia Reversa e Descompilação de GBA (Summon Night: Swordcraft Story)

Atue como um especialista em Engenharia Reversa de Game Boy Advance (arquitetura ARM7TDMI / THUMB), descompilação (*matching decomp*) e desenvolvimento em C/Assembly.

Nosso objetivo é iniciar a engenharia reversa e descompilação da ROM do jogo **Summon Night: Swordcraft Story** (GBA), com dois objetivos principais:
1. Mapear e extrair toda a engine de texto, fontes e scripts de eventos para permitir uma localização completa em Português (PT-BR) sem limites de memória.
2. Estruturar o código desmontado (disassembly) e descompilado em C para documentar o funcionamento interno do jogo, abrindo caminho para modificações profundas ou um futuro port nativo (via SDL2).

## Etapas de Trabalho
1. **Setup do Ambiente:** Configurar ferramentas de análise e disassembly para GBA (usando Python, `capstone` para disassembly ARM/THUMB, ou integração com ferramentas de decomp/Ghidra).
2. **Mapeamento da ROM:** Separar o binário entre código executável (ARM/THUMB), tabelas de dados, gráficos (tilesets/sprites) e bancos de script/diálogo.
3. **Engenharia Reversa do Sistema de Texto:** Encontrar a função de renderização de texto e leitura de strings para entender como o jogo calcula larguras de fonte, ponteiros e códigos de controle.
4. **Reconstrução Modular:** Extrair os bancos de texto para arquivos legíveis que possam ser traduzidos e recompilados de volta na ROM.

## Primeiro Passo
Crie a estrutura inicial de pastas do projeto (`rom/`, `tools/`, `docs/`, `extracted/`, `src/`) e escreva um script em Python para inspecionar o cabeçalho da ROM de GBA, identificar o ponto de entrada (*Entry Point*) e mapear a distribuição de dados e espaço livre no binário.