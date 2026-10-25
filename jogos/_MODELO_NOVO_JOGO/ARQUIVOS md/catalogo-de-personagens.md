# 🎭 Catálogo de Personagens e NPCs — Biografia Híbrida & Tom de Voz
**Jogo:** [NOME DO JOGO]  
**Plataforma:** GBA / [CONSOLA]  
**Status do Catálogo:** Em Construção  

Este catálogo estabelece as **diretrizes biográficas, psicológicas e estilísticas de localização** para cada personagem e NPC do jogo. É construído combinando os dados extraídos diretamente da ROM com pesquisas canônicas em fontes oficiais da web (artbooks, wikis canônicas, manuais originais), garantindo que a tradução em PT-BR mantenha autenticidade, humor e voz única para cada falante.

---

## 📌 Guia de Registro e Tom de Voz (Localization Tone Guidelines)

| Registro de Fala | Características Gramaticais / Vocabulário em PT-BR | Exemplo de Aplicação |
| :--- | :--- | :--- |
| **Erudito / Aristocrático** | Uso de mesóclises ou ênclises formais, pronomes de tratamento respeitosos, ausência de gírias. | Reis, magos anciãos, nobres, deuses. |
| **Militar / Disciplinado** | Frases curtas, imperativas, termos táticos, tom seco e objetivo. | Capitães da guarda, cavaleiros, generais. |
| **Coloquial / Jovem** | Contrações naturais (*tá*, *pra*, *cê*), gírias leves contemporâneas, exclamações frequentes. | Protagonistas jovens, aprendizes, crianças. |
| **Rústico / Operário** | Regionalismos suaves, termos da profissão (forja, marcenaria), informalidade acolhedora. | Ferreiros, mineradores, marinheiros. |
| **Sarcástico / Ladino** | Ironia, trocadilhos, apelidos provocativos, uso de reticências para insinuar algo. | Ladrões, rivais arrogantes, anti-heróis. |
| **Infantil / Mascote** | Fala na terceira pessoa, onomatopeias, repetição de sílabas, frases inocentes. | Mascotes, espíritos elementais, bebês monstros. |

---

## 👤 Modelo de Ficha de Personagem (Template Individual)

### `[ID_PERSONAGEM]` — [Nome Original] ➔ **[Nome PT-BR Adotado]**

#### 1. Identificação Básica
- **Nome Original (JP):** [Ex: クレル (Kureru)]
- **Nome Ocidental (EN):** [Ex: Cleru]
- **Nome Oficial Adotado (PT-BR):** [Ex: Cleru]
- **Papel na Trama:** Protagonista Masculino / Aprendiz de Ferreiro
- **Gênero:** Masculino | **Faixa Etária Estimada:** 14–15 anos
- **Afiliação / Localização Principal:** Oficina de Forja, Guilda Prateada

#### 2. Biografia Híbrida
- **🔍 Informações Extraídas da ROM:**
  - Filho do lendário Mestre Shintetsu, que desapareceu misteriosamente há 3 anos.
  - Começa o jogo sem arma própria e precisa invocar uma Fera Guardiã na cerimônia oficial.
  - Determinado a vencer o torneio da cidade para honrar o nome de seu pai.
- **🌐 Pesquisa Canônica na Web (Wikis / Artbooks Oficiais):**
  - *(Fonte: Summon Night Official World Guide / Wiki Canônica)*
  - Personalidade calorosa, impetuosa, por vezes ingênua ao lidar com intenções maliciosas alheias.
  - Possui complexo de inferioridade em relação à genialidade do pai, mas compensa com esforço físico incansável.
  - Não suporta ver amigos em perigo e desafia ordens superiores para resgatá-los.

#### 3. Perfil Psicológico e Tom de Voz (Idioleto)
- **Tom de Voz Geral:** Jovem, enérgico, corajoso e leal. Em momentos cotidianos é brincalhão; sob pressão, torna-se focado e resoluto.
- **Forma de Tratamento:**
  - *Com Mestres e Idosos:* Trata com respeito sincero (*"Mestre Bron"*, *"Senhor"*), mas sem excesso de cerimônia burocrática.
  - *Com o Rival:* Responde a provocações na mesma moeda, sem perder a compostura moral.
  - *Com a Fera Guardiã:* Trata como parceiro igual, confiando sua vida cegamente à criatura.
- **Cacoetes e Expressões Recorrentes:**
  - Usa interjeições como *"Caramba!"*, *"Vamos nessa!"*, *"Não vou desistir de jeito nenhum!"*.
- **O que EVITAR na Tradução:**
  - Não traduzir suas falas de forma excessivamente formal ou pomposa.
  - Não usar gírias hiper-modernas que envelheçam mal (ex: gírias de internet temporárias).

---

## 👥 Registro dos Personagens Principais (Sumário Rápido)

| ID | Nome EN | Nome PT-BR | Papel / Arquétipo | Registro de Fala | Maneirismo / Traço Marcante |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CHR_01` | Protagonista Masc. | *Cleru* | Herói jovem e determinado | Coloquial / Enérgico | Fala entusiasmada, dedicado à forja |
| `CHR_02` | Protagonista Fem. | *Pratty* | Heroína esperta e corajosa | Coloquial / Expressiva | Levemente impaciente, maternal com parceiro |
| `CHR_03` | Mentor | *Mestre Bron* | Mestre ferreiro veterano | Rústico / Austero mas caloroso | Fala rouca, broncas carinhosas, exige dedicação |
| `CHR_04` | Rival | *Varil / Chaves* | Concorrente arrogante | Sarcástico / Superior | Desdenha novatos, confia cegamente na linhagem |
| `CHR_05` | Mascote / Guardião | *Kutty* | Criatura elemental fofa | Infantil / Onomatopeico | Repete o próprio nome (*"Kutty! Kuuu!"*) |

---

## 🌾 Registro de NPCs Secundários e Habitantes

| NPC / ID | Localização | Função no Mundo | Comportamento e Tom de Conversa |
| :--- | :--- | :--- | :--- |
| **Comerciante da Guilda** | Térreo da Guilda | Venda de matérias-primas | Vendedor afável, sempre pronto a oferecer pechinchas e dicas. |
| **Guarda do Portão** | Entrada do Labirinto | Controle de acesso ao calabouço | Rígido, alerta para o perigo constante das feras errantes. |
| **Criança da Praça** | Perto do Chafariz | Fofocas e rumores de missões | Curiosa, empolgada com a presença de guerreiros famosos. |
