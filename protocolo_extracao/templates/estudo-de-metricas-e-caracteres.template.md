# 📐 Estudo de Métricas de Caracteres por Linha de Diálogo
**Jogo:** [NOME DO JOGO]  
**Plataforma:** Game Boy Advance (GBA)  
**Fonte Original:** [Monoespaçada / Proporcional VWF]  
**Largura da Caixa no Jogo:** [ex: 216] pixels úteis  
**Status do Estudo:** Calibrado  

---

## 🎯 1. Objetivo do Estudo

Garantir que **100% dos textos traduzidos para Português do Brasil caibam com perfeição visual dentro das caixas de diálogo do jogo**, eliminando problemas de:
1. **Overflow:** Texto ultrapassando a borda da moldura ou sumindo fora da tela.
2. **Auto-Wrap Quebrado:** A engine cortando palavras ao meio por falta da quebra manual `<br>`.
3. **Desperdício Visual:** Textos excessivamente curtos que deixam caixas vazias ou exigem mais janelas que o necessário.

---

## 📏 2. Parâmetros Físicos da Tela e Caixa de Texto

| Parâmetro de Hardware / Engine | Medida Original | Observações Técnicas |
| :--- | :--- | :--- |
| **Resolução Nativa da Tela** | 240 x 160 pixels | Padrão absoluto do display do GBA. |
| **Dimensão Total da Caixa de Diálogo** | [ex: 232 x 48] pixels | Área ocupada pelo balão de fala ou janela BG. |
| **Bordas / Margens Internas (Padding)** | [ex: 8px esq. / 8px dir.] | Espaço reservado para moldura de tiles. |
| **Largura Útil de Renderização de Texto** | **[ex: 216] pixels** | Largura real disponível para os glifos. |
| **Linhas Visíveis por Caixa** | [ex: 2 a 3 linhas] | Linhas exibidas simultaneamente antes do scroll/avanço. |
| **Tipo de Fonte Utilizada** | [Fixed 8x8 / VWF] | Define se a contagem é fixa ou proporcional. |
| **Largura Média do Glifo PT-BR** | [ex: 6.2 px (VWF)] | Média ponderada com caracteres acentuados. |

---

## 📊 3. Análise Estatística do Texto Original (Original vs Tradução Sugerida)

> Executado automaticamente pelo utilitário `metrics_analyzer.py` sobre o lote de diálogos extraídos da ROM:

### Estatísticas Globais de Diálogos

| Métrica | Texto Original (EN/JP) | Tradução em PT-BR (Estimada/Real) | Variação (%) |
| :--- | :---: | :---: | :---: |
| **Total de Caixas de Diálogo** | `[ex: 3.420]` | `[ex: 3.420]` | `0%` |
| **Total de Linhas Renderizadas** | `[ex: 7.840]` | `[ex: 8.120]` | `+3.5%` |
| **Média de Caracteres por Linha** | `[ex: 29.4]` | `[ex: 31.8]` | `+8.1%` |
| **Comprimento Mínimo de Linha** | `[ex: 2 chars]` | `[ex: 2 chars]` | `0%` |
| **Comprimento Máximo de Linha** | `[ex: 36 chars]` | `[ex: 37 chars]` | `+2.7%` |
| **Média de Linhas por Caixa** | `[ex: 2.29]` | `[ex: 2.37]` | `+3.4%` |

---

## 🎯 4. Tabela de Limites e Recomendações para a Tradução

Com base na largura útil da caixa de diálogo e na tabela de larguras de glifos da fonte PT-BR, os seguintes limites operacionais devem ser respeitados pelo tradutor e pela IA:

| Nível de Alerta | Caracteres por Linha (PT-BR) | Status Visual no App Validador | Ação Recomendada |
| :--- | :---: | :---: | :--- |
| 🟢 **Ideal (Zona Confortável)** | **1 a 32 caracteres** | Verde | Texto com leitura fluida e margem estética perfeita. |
| 🟡 **Atenção (Soft Limit)** | **33 a 35 caracteres** | Amarelo | Próximo à borda. Permitido se a frase contiver letras finas (*i, l, t*). |
| 🔴 **Estouro (Hard Limit)** | **36+ caracteres** | Vermelho | **PROIBIDO**. O texto sofrerá corte ou estourará a moldura física. |

### Regras de Quebra de Linha:
1. Toda mudança de linha física dentro da mesma caixa de diálogo **deve conter a tag `<br>`**.
2. **Máximo de [3] linhas por caixa de diálogo**. Nunca inserir um 4º `<br>` dentro de uma mesma entrada de tabela, pois a engine do jogo sobrescreverá a primeira linha ou cortará a parte inferior.
3. Se a tradução em PT-BR exceder o limite de linhas ou caracteres da caixa original, divida a fala ou utilize sinônimos mais concisos (evitar prolixidade).

---

## 🧪 5. Casos Especiais de Renderização

- **Nomes Dinâmicos (`{PLAYER}`, `{PARTNER}`):**
  - A tag `{PLAYER}` no script original ocupa 8 caracteres (`{PLAYER}`), mas no jogo pode ser preenchida com um nome de até **10 a 12 letras**.
  - Sempre reserve uma folga de **4 a 6 caracteres a menos** em linhas que contenham tags dinâmicas para evitar overflow quando o jogador utilizar um nome longo.
- **Pontuação e Espaçamento:**
  - Reticências (`...`) devem ser mantidas como 3 pontos normais ou o caractere especial único da ROM se suportado.
  - Não deixe espaços vazios antes ou depois da tag `<br>`. Exemplo correto: `Primeira linha`<br>`Segunda linha`.
