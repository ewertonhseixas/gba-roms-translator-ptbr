---
name: gba-qa-gate
description: >-
  Executa o Funil de Qualidade e Auditoria Completa (Quality Gate) em arquivos ou pastas
  de tradução (.md). Combina qa_gate_hook.py e metrics_analyzer.py com revisão pente-fino
  para eliminar overflows de linha (>35 chars), choques de gênero no protagonista, tags
  quebradas, orfandade textual e termos fora do glossário. Use quando o usuário pedir para
  revisar, validar ou auditar a qualidade da tradução.
---

# 🛡️ Skill: Funil de Qualidade & Quality Gate (`gba-qa-gate`)

Inspirada nos *Quality Gates* de pré-commit e revisão do *Claude-Code-Game-Studios*, esta skill executa a bateria oficial de validação do **GBA Localization Studio**.

## 📋 Procedimento de Auditoria em 4 Etapas

### Etapa 1: Varredura com o `qa_gate_hook.py`
Execute o script de Quality Gate sobre o arquivo específico ou sobre toda a pasta `ARQUIVOS md` do jogo:
```powershell
python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/qa_gate_hook.py" "<caminho_alvo>" -l 35
```
O script verificará automaticamente:
- **Gate 1 (Tags):** Paridade exata de `{PLAYER}`, `{PARTNER}`, `[0x05]`, etc. entre original e PT-BR.
- **Gate 2 (Overflow):** Qualquer linha individual entre `<br>` acima do limite de caracteres.
- **Gate 3 (Orfandade):** Artigos e preposições (`o`, `a`, `de`, `em`, `e`, `que`) pendurados no fim da linha antes de `<br>`.
- **Gate 4 (Abreviações):** Uso indevido de abreviações em lotes de história.
- **Gate 5 (Neutralidade):** Expressões suspeitas de marcação de gênero masculino no protagonista.

### Etapa 2: Relatório Estatístico Global (`metrics_analyzer.py`)
Gere ou atualize o relatório `estudo-de-metricas-e-caracteres.md` do jogo para verificar a saúde estatística (Média, Máximo e Percentil 95 de largura de linha):
```powershell
python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/metrics_analyzer.py" -d "<pasta_ARQUIVOS_md>" -g "<Nome_do_Jogo>" -l 35
```

### Etapa 3: Correção Cirúrgica de Erros e Alertas
Para cada erro `🔴` ou alerta `🟡` relevante apontado nos passos anteriores:
1. Abra o arquivo `.md` nas linhas indicadas.
2. Reescreva a frase mantendo a naturalidade dramática e o idioleto do personagem, sem mutilar palavras.
3. Re-execute o `qa_gate_hook.py` até que o resultado seja **0 erros críticos**.

### Etapa 4: Chancela de Validação
- Com todos os testes verdes, atualize o status das linhas revisadas para `✅ Validado` e informe ao usuário que o lote está pronto para compilação na ROM (`gba-rom-build-verify`).
