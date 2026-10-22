# 02 — Glossário Oficial, Personagens, Guardiões e Locais

Este documento reúne todos os **nomes próprios, títulos do universo do jogo, variáveis dinâmicas de texto e nomes de locais/mapas** extraídos diretamente da ROM (`0x08071BCC`–`0x08073C8C`), acompanhados das **traduções e convenções sugeridas** para validação.

---

## 1. Variáveis Dinâmicas da Engine de Texto (`0x83C0`–`0x83C5`)

Na engine de texto (`Text_FetchNextChar` @ `0x08009C38`), os códigos `83 C0` a `83 C5` são substituídos dinamicamente em tempo de execução conforme a escolha de protagonista e Fera Guardiã:

| Tag no Script | Código Hex (LE) | Valor Padrão (EN-US) | Tradução / Adaptação Sugerida (PT-BR) | Observações | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `{PLAYER}` | `0xC083` (`83 C0`) | `Cleru / Pratty` | `Cleru / Pratty` | Nome do(a) protagonista escolhido(a) pelo jogador. | ✅ Validado |
| `{PARTNER}` | `0xC183` (`83 C1`) | `Rasho / Sanary / Sugar / Kutty` | `Rasho / Sanary / Sugar / Kutty` | Nome da Fera Guardiã (*Guardian Beast*) parceira. | ✅ Validado |
| `{VAR_2}` | `0xC283` (`83 C2`) | `Mantém {VAR_2}` | `Mantém {VAR_2}` | Preenchido automaticamente pelo jogo com o nome da técnica/efeito (ex: `Aprendeu {VAR_2}!`). | ✅ Validado |
| `{SIBLING}` | `0xC383` (`83 C3`) | `Big Bro / Big Sis` (`0x0807288C`) | `Maninho / Maninha` | Forma carinhosa usada por certos NPCs/personagens para se referir ao protagonista. | ✅ Validado |
| `{VAR_4}` | `0xC483` (`83 C4`) | `Mantém {VAR_4}` | `Mantém {VAR_4}` | Preenchido automaticamente pelo jogo com o nome da magia aprendida (ex: `Aprendeu {VAR_4}!`). | ✅ Validado |
| `{MASTER}` | `0xC583` (`83 C5`) | `Hayato / Touya / Natsumi / Aya` | `Hayato / Touya / Natsumi / Aya` | Nomes de invocadores/mestres referenciados no sistema. | ✅ Validado |

---

## 2. Termos Fundamentais do Universo (*Lore & Sistema*)

Para manter a identidade de **Summon Night: Swordcraft Story**, abaixo estão as recomendações para os termos centrais da obra (você pode validar se prefere manter termos como *Craftknight* / *Craftlord* em inglês ou traduzi-los):

| Termo Original (EN-US) | Tradução Sugerida (Opção A — Adaptada) | Alternativa (Opção B — Híbrida/Original) | Contexto no Jogo | Status |
| :--- | :--- | :--- | :--- | :---: |
| **Craftknight** | **Craftknight** | **Craftknight** | Guerreiros-ferreiros que forjam suas próprias armas e lutam com elas. | ✅ Validado |
| **Craftlord** | **Craftlord** | **Craftlord** | Os 7 grandes mestres ferreiros que protegem e governam Wystern. | ✅ Validado |
| **Craftlord of Iron** | **Craftlord of Iron** | **Craftlord do Ferro** | Título de Shintetsu (pai do protagonista). | ✅ Validado |
| **Craftlord of Sapphire** | **Craftlord of Sapphire** | **Craftlord da Safira** | Título de Mestre Sakuro. | ✅ Validado |
| **Craftlord of Ruby** | **Craftlord of Ruby** | **Craftlord do Rubi** | Título de Mestra Kouren. | ✅ Validado |
| **Guardian Beast** | **Guardian Beast** | **Guardian Beast** | Criatura invocada que auxilia o protagonista na forja e nas batalhas. | ✅ Validado |
| **Summon Creature / Summon Beast** | **Summon Creature / Summon Beast** | **Criatura Summon** | Seres chamados de outros mundos (Lyndbaum / Silturn / Sapureth, etc.). | ✅ Validado |
| **Stray Summon ("Stray")** | **Stray Summon ("Stray")** | **Summon Errante** | Criatura invocada que perdeu seu mestre e vaga pelo Labirinto. | ✅ Validado |
| **Mystic Ore** | **Mystic Ore** | **Minério Místico** | Minério raro que transforma uma arma comum em elemental/especial. | ✅ Validado |
| **Summonite** | **Summonite** | **Summonite** | Joia/mineral usado para invocar a Fera Guardiã. | ✅ Validado |
| **City of Swords** | **City of Swords** | **Cidade das Espadas** | Epíteto da cidade marítima de Wystern. | ✅ Validado |
| **Silver Guild** | **Silver Guild** | **Silver Guild** | Guilda do Mestre Bron, onde o protagonista treina no início. | ✅ Validado |
| **Gold Guild** | **Gold Guild** | **Gold Guild** | Guilda rival localizada no andar intermediário de Wystern. | ✅ Validado |
| **Central Tower** | **Central Tower** | **Torre Central** | Castelo dos Craftlords no coração de Wystern, sede do torneio. | ✅ Validado |
| **Water Scooter** | **Water Scooter** | **Water Scooter** | Veículo usado para navegar pelos canais de água de Wystern. | ✅ Validado |

---

## 3. Personagens e Feras Guardiãs (`0x08071BCC`–`0x08072D04`)

| Endereço ROM | Nome Original (EN-US) | Nome Sugerido (PT-BR) | Papel no Jogo | Status |
| :--- | :--- | :--- | :--- | :---: |
| `0x08072444` / `0x08072CB0` | `Cleru` | `Cleru` | Protagonista masculino. | ✅ Validado |
| `0x08072450` / `0x08072CA0` | `Pratty` | `Pratty` | Protagonista feminina. | ✅ Validado |
| `0x08072460` / `0x08072D04` | `Zantek` | `Zantek` | Fera Guardiã (personagem especial/sistema). | ✅ Validado |
| `0x08072470` / `0x08072CF8` | `Rasho` | `Rasho` | Fera Guardiã do mundo de Silturn (Oni rebelde, elemento Fogo). | ✅ Validado |
| `0x08071C38` | `Sanary` | `Sanary` | Fera Guardiã / Rival (Demônio feminina vaidosa / ou personagem rival). | ✅ Validado |
| `0x0807247C` / `0x08072CEC` | `Sugar` | `Sugar` | Fera Guardiã do mundo de Sapureth (Fada/Anjo dedicada, elemento Água). | ✅ Validado |
| `0x08072488` / `0x08072CE0` | `Kutty` | `Kutty` | Fera Guardiã do mundo de Maetropa (Criatura peluda que fala "Kutty"/"Kuu", Vento). | ✅ Validado |
| `0x08072494` / `0x08072CD0` | `Kuhyra` | `Kuhyra` | Fera Guardiã especial. | ✅ Validado |
| `0x08071C78` | `Chaves` | `Chaves` | Rival do 1º combate do torneio (usa espada gigante). | ✅ Validado |
| `0x08071C60` | `Kenon` | `Kenon` | Rival do 2º combate do torneio (usa machado). | ✅ Validado |
| `0x08071C54` | `Razzy` | `Razzy` | Rival do 3º combate do torneio (garota que usa soqueiras). | ✅ Validado |
| `0x08071C48` | `Ariel` | `Ariel` | Rival do 4º combate (ao lado de Mariel; usa broca). | ✅ Validado |
| `0x08071C6C` | `Varil` | `Varil` | Rival principal da Guilda Dourada (usa lança). | ✅ Validado |
| `0x08071BF0` | `Craftlord Lubert` | `Craftlord Lubert` | Lorde Artesão especialista em Brocas/Tecnologia. | ✅ Validado |
| `0x08071C14` | `Craftlord Ureksa` | `Craftlord Ureksa` | Lorde Artesão antagonista da Guilda Dourada (usa lança). | ✅ Validado |
| `0x08071BCC` | `Deigleya Soldier` | `Deigleya Soldier` | Soldado inimigo militar. | ✅ Validado |
| `0x0807288C` | `Big Bro` | `Maninho` | Variável `{SIBLING}` (quando jogando com Cleru). | ✅ Validado |
| `0x0807289C` | `Big Sis` | `Maninha` | Variável `{SIBLING}` (quando jogando com Pratty). | ✅ Validado |
| `0x080728AC` | `Hayato` | `Hayato` | Nome padrão `{MASTER}` 1. | ✅ Validado |
| `0x080728BC` | `Touya` | `Touya` | Nome padrão `{MASTER}` 2. | ✅ Validado |
| `0x080728C8` | `Natsumi` | `Natsumi` | Nome padrão `{MASTER}` 3. | ✅ Validado |
| `0x080728D8` | `Aya` | `Aya` | Nome padrão `{MASTER}` 4. | ✅ Validado |

---

## 4. Locais, Cidades, Oficinas e Andares do Labirinto (`0x08071F08`–`0x08073C8C`)

| Endereço ROM | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :---: |
| `0x08071F08` | `Labyrinth 2` | `Labirinto 2` | ✅ Validado |
| `0x08071F20` | `Fort Mirana Docks` | `Fort Mirana Docks` | ✅ Validado |
| `0x08071F44` / `0x08072D44` | `Fort Mirana` | `Fort Mirana` | ✅ Validado |
| `0x08071F5C` | `Lighthouse Rooftop` | `Lighthouse Rooftop` | ✅ Validado |
| `0x08071F84` / `0x08072D5C` | `Cape Lighthouse` | `Cape Lighthouse` | ✅ Validado |
| `0x08071FA4` / `0x08072D7C` | `Marine Dungeon` | `Marine Dungeon` | ✅ Validado |
| `0x08071FC4` / `0x08072EE4` | `Upper Wystern` | `Upper Wystern` | ✅ Validado |
| `0x08072F00` | `Middle Wystern` | `Middle Wystern` | ✅ Validado |
| `0x08071FE0` / `0x08072F20` | `Lower Wystern` | `Lower Wystern` | ✅ Validado |
| `0x08071FFC` / `0x08072D9C` | `Labyrinth` | `Labirinto` | ✅ Validado |
| `0x08072010` | `Battle Arena` | `Arena de Batalha` | ✅ Validado |
| `0x08072D14` | `Ship Workshop` | `Ship Workshop` | ✅ Validado |
| `0x08072D30` | `Ship Helm` | `Ship Helm` | ✅ Validado |
| `0x08072DB0` | `Mirana` | `Mirana` | ✅ Validado |
| `0x08072DC0` | `Vance Cape` | `Vance Cape` | ✅ Validado |
| `0x08072DD8` | `Kagro Volcano` | `Kagro Volcano` | ✅ Validado |
| `0x08072DF4` | `Rugista Island` | `Rugista Island` | ✅ Validado |
| `0x08072E14` | `Central Tower 4F` | `Central Tower 4ºA` | ✅ Validado |
| `0x08072E38` | `Central Tower 3F` | `Central Tower 3ºA` | ✅ Validado |
| `0x08072E5C` | `Central Tower 2F` | `Central Tower 2ºA` | ✅ Validado |
| `0x08072E80` | `Central Tower 1F` | `Central Tower 1ºA` | ✅ Validado |
| `0x08072EA4` | `Silver Guild 2F` | `Silver Guild 2ºA` | ✅ Validado |
| `0x08072EC4` | `Silver Guild 1F` | `Silver Guild 1ºA` | ✅ Validado |
| `0x08072F48` | `Rumari's House` | `Casa de Rumari` | ✅ Validado |
| `0x08072F68` | `Hideout` | `Esconderijo` | ✅ Validado |
| `0x08072F78` | `Mayor's House` | `Casa do Prefeito` | ✅ Validado |
| `0x08072F94` | `Hidden Room` | `Hidden Room` | ✅ Validado |
| `0x08072FAC` | `Assembly Hall` | `Assembly Hall` | ✅ Validado |
| `0x08072FC8` | `Arena` | `Arena` | ✅ Validado |
| `0x08072FD4` | `Workshop` | `Workshop` | ✅ Validado |
| `0x08072FE8` | `Trish Workshop` | `Trish Workshop` | ✅ Validado |
| `0x08073008` | `Cazio Workshop` | `Cazio Workshop` | ✅ Validado |
| `0x08073028` | `Ariel/Mariel Lab` | `Ariel/Mariel Lab` | ✅ Validado |
| `0x0807304C` | `Razzy Workshop` | `Razzy Workshop` | ✅ Validado |
| `0x0807306C` | `Sanary Workshop` | `Sanary Workshop` | ✅ Validado |
| `0x0807308C` | `My Workshop` | `Minha Oficina` | ✅ Validado |
| `0x080730A4` | `Rondeau's House` | `Casa de Rondeau` | ✅ Validado |
| `0x080730C4` | `Gold Guild` | `Gold Guild` | ✅ Validado |
| `0x080730DC` | `Sakuro's House` | `Casa de Sakuro` | ✅ Validado |
| `0x080730FC` | `Port` | `Port` | ✅ Validado |
| `0x08073108` | `House` | `Casa` | ✅ Validado |
| `0x08073114` | `Inn` | `Pousada` | ✅ Validado |
| `0x0807311C` | `Weapon Shop` | `Loja de Armas` | ✅ Validado |
| `0x08073134` | `Item Shop` | `Loja de Itens` | ✅ Validado |
| `0x08073148` | `Home` | `Quarto` | ✅ Validado |
| `0x08073B04` | `Labyrinth  1F` | `Labirinto  1ºA` | ✅ Validado |
| `0x08073B20` | `Labyrinth  3F` | `Labirinto  3ºA` | ✅ Validado |
| `0x08073B3C` | `Labyrinth  6F` | `Labirinto  6ºA` | ✅ Validado |
| `0x08073B58` | `Labyrinth 11F` | `Labirinto 11ºA` | ✅ Validado |
| `0x08073B74` | `Labyrinth 18F` | `Labirinto 18ºA` | ✅ Validado |
| `0x08073B90` | `Labyrinth 26F` | `Labirinto 26ºA` | ✅ Validado |
| `0x08073BAC` | `Labyrinth 31F` | `Labirinto 31ºA` | ✅ Validado |
| `0x08073BC8` | `Labyrinth 37F` | `Labirinto 37ºA` | ✅ Validado |
| `0x08073BE4` | `Labyrinth 45F` | `Labirinto 45ºA` | ✅ Validado |
| `0x08073C00` | `Labyrinth 50F` | `Labirinto 50ºA` | ✅ Validado |
| `0x08073C1C` | `Labyrinth 56F` | `Labirinto 56ºA` | ✅ Validado |
| `0x08073C38` | `Labyrinth 66F` | `Labirinto 66ºA` | ✅ Validado |
| `0x08073C54` | `Labyrinth 76F` | `Labirinto 76ºA` | ✅ Validado |
| `0x08073C70` | `Labyrinth 86F` | `Labirinto 86ºA` | ✅ Validado |
| `0x08073C8C` | `Labyrinth 96F` | `Labirinto 96ºA` | ✅ Validado |