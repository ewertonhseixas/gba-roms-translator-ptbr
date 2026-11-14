---
name: gba-rom-build-verify
description: >-
  Executa o pipeline seguro de compilação da ROM PT-BR, auditoria de imagens com texto
  (image_text_auditor.py), geração de patch IPS/BPS e verificação pós-build. Use quando
  o usuário pedir para compilar a ROM, injetar traduções no jogo, gerar o patch IPS ou
  testar as alterações no emulador/port.
---

# 🎮 Skill: Compilação Segura da ROM & Verificação (`gba-rom-build-verify`)

Este playbook coordena a etapa final do pipeline de engenharia do **GBA Localization Studio**, garantindo que textos e gráficos validados sejam injetados na ROM sem corromper ponteiros ou transparências de hardware.

## 📋 Passo a Passo de Compilação e Verificação

### Passo 1: Pré-Build Quality Gate
Antes de injetar qualquer texto na ROM, execute uma checagem rápida nos arquivos `.md` que foram modificados recentemente:
```powershell
python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/qa_gate_hook.py" "<pasta_ARQUIVOS_md_ou_arquivo>" -l 36
```

### Passo 2: Auditoria de Gráficos Editados (Se Aplicável)
Se houve edição de PNGs (Tela de Título, Menus, Game Over), audite a integridade das dimensões e paletas antes da reinjeção:
```powershell
python "02_TRADUCAO_ROMS_GBA/protocolo_extracao/tools/image_text_auditor.py" -d "<pasta_graphics>" -o "<pasta_ARQUIVOS_md>/controle-de-imagens-com-texto.md"
```
- Confirme que nenhuma imagem teve sua resolução alterada e que o índice 0 da paleta permaneceu intacto (transparente).

### Passo 3: Compilação da ROM PT-BR e Geração do Patch `.ips`
1. Execute o script de build oficial do jogo (ex: `Compilar_ROM_PTBR.bat` ou o compilador Python correspondente na pasta `tools/` do jogo).
2. Verifique no log de saída:
   - Total de strings/blocos injetados com sucesso.
   - Ausência de erros de estouro de buffer ou colisão de ponteiros (`0x08XXXXXX`).
   - Confirmação de que a ROM original permaneceu intocada e que a nova ROM `*_PTBR.gba` e o patch `.ips` em `releases/` foram atualizados.

### Passo 4: Atualização de Versionamento e Changelog
- Se for uma entrega de marco ou lote concluído, registre as mudanças no `CHANGELOG.md` e `VERSION.json` do projeto do jogo.
