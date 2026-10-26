# 📜 Protocolo de Tradução e Localização do Jogo (PT-BR)
**Jogo:** [Nome do Jogo / ROM Base]  
**Plataforma:** Game Boy Advance (GBA) / Retrô  
**Status:** Diretriz Ativa de Tradução  

> Consulte as normas completas e especificações técnicas detalhadas no [Protocolo Mestre de Tradução](../../protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md).

---

## 🏛️ 1. Diretrizes Vitais de Localização

0. **Fase 0: Pré-Tradução Obrigatória:** É proibido iniciar a tradução de diálogos sem antes preencher o `ARQUIVOS md/catalogo-de-personagens.md`, fixando idade, ocupação, registro formal/informal, bordões e tom de voz de cada falante.
1. **Perfil de Personagens (*Character Voice*):** Adequar o vocabulário e ritmo à personalidade de cada falante registrado no catálogo da fase de pré-tradução.
2. **Neutralidade de Gênero:** Em textos de protagonista compartilhados pelo motor do jogo, priorizar fórmulas epicenas, construções verbais e substantivos para evitar concordâncias masculinas forçadas.
3. **Eliminação do Inglês:** Traduzir 100% dos textos de interface, sistema, combate e diálogos. Manter em inglês estritamente os nomes próprios de pessoas e mundos de fantasia.
4. **Coerência Absoluta:** Seguir a tabela unificada em `ARQUIVOS md/02-glossario-e-terminologias.md`.
5. **Regra de Abreviações:**
   - **Diálogos:** Tolerância zero para abreviações. O texto deve ser reescrito com palavras concisas.
   - **Menus/Itens:** Abreviações padronizadas conforme tabela canônica do framework (`ATQ`, `DEF`, `Recup.`, etc.).
6. **Ciclo de Termos Adaptados:**
   - Introdução com tradução completa explicativa.
   - Uso comum subsequente na versão adaptada curta para economia de caracteres.

---

## 📐 2. Limites Operacionais de Tela (Hardware)

- **Hard Limit:** 36 caracteres/linha (teto absoluto antes do clipping visual).
- **Zona Segura:** 1 a 32 caracteres/linha.
- **Zona de Atenção:** 33 a 35 caracteres/linha (verificar largura de glifos).
- **Orfandade Proibida:** Não deixar artigos ou preposições isolados no fim da linha.

---

## 📌 3. Checklist de Liberação de Lote

- [ ] O **Catálogo de Personagens** foi previamente consultado antes de iniciar a tradução das falas?
- [ ] Todas as linhas respeitam a métrica máxima de caracteres?
- [ ] O texto soa natural para um falante nativo do Brasil?
- [ ] A concordância de gênero neutro foi mantida em falas compartilhadas?
- [ ] Todo texto em inglês de sistema e menus foi eliminado?
- [ ] As tags dinâmicas (`{PLAYER}`, `{PARTNER}`, etc.) continuam intactas?
- [ ] Nenhum diálogo contém palavras abreviadas?
