---
name: gba-character-bible
description: >-
  Executa a Fase 0 obrigatória do Protocolo Mestre de Tradução: mapeia todos os falantes
  da ROM, pesquisa o lore oficial da franquia e constrói ou atualiza o Catálogo de Personagens
  (catalogo-de-personagens.md) e o Glossário (02-glossario) com o Tom de Voz (Character Voice),
  grau de formalidade, maneirismos e tratamento interpessoal. Use antes de traduzir novos capítulos.
---

# 🎭 Skill: Bíblia de Personagens & Glossário (`gba-character-bible`)

De acordo com a **Regra de Ouro da Pré-Tradução** ([PROTOCOLO_MESTRE_TRADUCAO.md](../../02_TRADUCAO_ROMS_GBA/protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md)), é terminantemente proibido traduzir diálogos sem antes catalogar os falantes. Esta skill guia a atuação do agente **Líder de Narrativa (`gba-narrative-lead`)** e do **Diretor de Localização (`gba-localization-director`)**.

## 📋 Passo a Passo de Execução

### Passo 1: Varredura de Falantes nos Lotes
1. Escaneie a coluna `Personagem / Contexto` dos arquivos Markdown de diálogos em `ARQUIVOS md/`.
2. Compare a lista de falantes encontrados com os já cadastrados em `ARQUIVOS md/catalogo-de-personagens.md`.

### Passo 2: Pesquisa de Biografia Híbrida (In-Game + Web Canônica)
Para cada personagem ainda não catalogado (ou com ficha incompleta):
1. Analise suas falas em inglês/japonês no dump para identificar seu vocabulário, idade aparente e relação com `{PLAYER}`.
2. Use `search_web` se necessário para consultar wikis oficiais da franquia e confirmar gênero, classe social e lore.

### Passo 3: Fixação do Idioleto (*Character Voice*)
Adicione ou atualize a entrada do personagem em `catalogo-de-personagens.md` definindo explicitamente:
- **Papel / Arquétipo:** (ex: Mestre Ferreiro, Aprendiz, Espírito Guardião, Rival Aristocrata, Vilão).
- **Gênero e Concordância:** Masculino fixo, Feminino fixo, ou Variável/Epiceno (como `{PLAYER}`).
- **Tom de Voz & Registro:**
  - *Mestres/Veteranos:* Solene, firme, paternal, rico em metáforas de forja e aço.
  - *Jovens/Aprendizes:* Coloquial limpo, ágil, energético, sem gírias datadas.
  - *Nobres/Rivais:* Elegante, altivo, irônico ou competitivo.
  - *Entidades/Fadas/Bestas:* Dengoso/infantil, arcaico/místico ou rústico/direto conforme a criatura.
- **Relações Interpessoais:** Como chama o protagonista e aliados.

### Passo 4: Sincronização com o Glossário
- Verifique se novos locais, títulos (*Craftlord -> Lorde Forjador*, *Craftknight -> Cavaleiro Forjador*), guildas ou materiais citados pelos personagens estão registrados em `02-glossario-e-terminologias.md` e alinhados ao [GLOSSARIO_GLOBAL_SUMMON_NIGHT.md](../../02_TRADUCAO_ROMS_GBA/protocolo_traducao/GLOSSARIO_GLOBAL_SUMMON_NIGHT.md).
