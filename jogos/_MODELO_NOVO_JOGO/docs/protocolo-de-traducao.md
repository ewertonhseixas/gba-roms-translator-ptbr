# 📜 Protocolo de Tradução e Localização do Jogo (PT-BR)
**Jogo:** [Nome do Jogo / ROM Base]  
**Plataforma:** Game Boy Advance (GBA) / Retrô  
**Status:** Diretriz Ativa de Tradução  

> Consulte as normas completas e especificações técnicas detalhadas no [Protocolo Mestre de Tradução](../../protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md).

---

## 🏛️ 1. Diretrizes Vitais de Localização

1. **Perfil de Personagens (*Character Voice*):** Adequar o vocabulário, formalidade e ritmo à idade, classe social e personalidade de cada falante registrado no `ARQUIVOS md/catalogo-de-personagens.md`.
2. **Neutralidade de Gênero:** Em textos de protagonista compartilhados pelo motor do jogo, priorizar fórmulas epicenas, construções verbais e substantivos para evitar concordâncias masculinas forçadas.
3. **Eliminação Integral do Inglês:** Traduzir e localizar 100% dos textos de interface, sistema, combate, armas, itens, magias, bestiário (monstros) e diálogos. Preservar no original estritamente nomes próprios puros de pessoas e mundos de fantasia.
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

- [ ] Todas as linhas respeitam a métrica máxima de caracteres?
- [ ] O texto soa natural para um falante nativo do Brasil?
- [ ] A concordância de gênero neutro foi mantida em falas compartilhadas?
- [ ] Todo texto em inglês de sistema, menus, armas, itens e monstros foi eliminado?
- [ ] Foram mantidos no original estritamente nomes próprios puros de pessoas e mundos?
- [ ] As tags dinâmicas (`{PLAYER}`, `{PARTNER}`, etc.) continuam intactas?
- [ ] Nenhum diálogo contém palavras abreviadas?
