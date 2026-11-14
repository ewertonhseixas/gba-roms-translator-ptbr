---
name: gba-new-game-kickoff
description: >-
  Inicia estruturadamente a extração e preparação de uma nova ROM de Game Boy Advance
  (ou console retrô) seguindo o Protocolo Mestre de Extração. Use esta skill quando o
  usuário quiser adicionar um novo jogo para tradução, dissecar uma ROM nova, mapear
  ponteiros/compressão ou gerar a estrutura inicial de arquivos Markdown.
---

# 🚀 Skill: Kickoff & Extração de Nova ROM GBA (`gba-new-game-kickoff`)

Este playbook executa o ciclo completo de inicialização de um novo projeto de tradução dentro de `02_TRADUCAO_ROMS_GBA/jogos/`, garantindo aderência total ao [Protocolo Mestre de Extração](../../02_TRADUCAO_ROMS_GBA/protocolo_extracao/PROTOCOLO_MESTRE_EXTRACAO.md).

## 📋 Passo a Passo de Execução

### Passo 1: Clonagem do Template Padronizado
1. Verifique se a pasta do jogo já existe em `02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/`.
2. Caso não exista, copie a estrutura de `02_TRADUCAO_ROMS_GBA/jogos/_MODELO_NOVO_JOGO/` para `02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/`.
3. Confirme que o arquivo `.gba` original encontra-se dentro de `rom/`. **Jamais modifique a ROM original in-place.**

### Passo 2: Fingerprint & Auditoria Binária da ROM
Execute o detector de recursos da suíte para mapear o cabeçalho, serial, espaço livre, compressões (LZ77/Huffman) e presença de vídeos (Mobiclip):
```powershell
python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/rom_feature_detector.py" "02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/rom/<arquivo.gba>" -o "02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/docs/relatorio-extracao.md"
```

### Passo 3: Extração Estruturada para os 5 Pilares Markdown
Construa ou execute os extratores específicos da engine na pasta `tools/` do jogo para popular `ARQUIVOS md/` com os arquivos obrigatórios compatíveis com o validador:
1. `02-glossario-e-terminologias.md`
2. `03-mensagens-do-sistema.md`
3. `06-itens-equipamentos-e-descricoes.md`
4. `catalogo-de-personagens.md`
5. Lotes sequenciais de diálogos (`08-`, `09-`, etc.) no formato:
   `| Script / Offset | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |`

### Passo 4: Calibração Matemática de Métricas e Imagens
1. Rode o analisador de métricas sobre os textos extraídos para estabelecer o **Soft Limit** e o **Hard Limit** da caixa de diálogo:
   ```powershell
   python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/metrics_analyzer.py" -d "02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/ARQUIVOS md" -g "<Nome do Jogo>" -l 36
   ```
2. Se houver gráficos extraídos em `extracted/graphics`, gere a planilha de controle de imagens:
   ```powershell
   python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/image_text_auditor.py" -d "02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/extracted/graphics" -o "02_TRADUCAO_ROMS_GBA/jogos/<Nome_Do_Jogo>/ARQUIVOS md/controle-de-imagens-com-texto.md"
   ```

### Passo 5: Handoff para a Fase 0 (Pré-Tradução)
- Informe ao usuário o resumo técnico da ROM extraída e acione a skill `gba-character-bible` antes de traduzir qualquer diálogo.
