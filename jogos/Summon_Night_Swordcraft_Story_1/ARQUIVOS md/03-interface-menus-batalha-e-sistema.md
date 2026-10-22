# 03 — Interface (UI), Menus, Batalha, Forja, Lojas e Sistema

Este documento contém **100% das strings de sistema, menus de pausa, batalha, forja, lojas, Modo Link (Multiplayer) e gerenciamento de Save** extraídas da faixa `0x08070FCC`–`0x08073ADC` e `0x081DD5AC`.

---

## 1. Comandos de Batalha, Pós-Batalha e Subida de Nível (`0x08070FCC`–`0x080717F4`)

| Endereço ROM | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Contexto / Notas | Status |
| :--- | :--- | :--- | :--- | :---: |
| `0x08070FCC` | `Command Help` | `Ajuda de Comandos` | Cabeçalho de ajuda no menu de batalha. | ✅ Validado |
| `0x0807100C` | `Attack 4` | `Ataque 4` | Slot de arma 4 em batalha. | ✅ Validado |
| `0x08071020` | `Attack 3` | `Ataque 3` | Slot de arma 3 em batalha. | ✅ Validado |
| `0x08071034` | `Attack 2` | `Ataque 2` | Slot de arma 2 em batalha. | ✅ Validado |
| `0x08071048` | `Attack 1` | `Ataque 1` | Slot de arma 1 em batalha. | ✅ Validado |
| `0x0807105C` | `Money` | `Dinheiro` | Recompensa financeira pós-batalha. | ✅ Validado |
| `0x08071068` | `Exp` | `EXP` | Experiência ganha. | ✅ Validado |
| `0x08071070` | `Item 2` | `Item 2` | Slot de espólio 2 pós-batalha. | ✅ Validado |
| `0x08071080` | `Item 1` | `Item 1` | Slot de espólio 1 pós-batalha. | ✅ Validado |
| `0x080711D0` | `Guard` | `Defesa` | Ação de guarda. | ✅ Validado |
| `0x0807162C` | `received!` | `recebido!` | Sufixo ao ganhar item/recompensa. | ✅ Validado |
| `0x08071640` | `{PLAYER} Level Up!` | `{PLAYER} subiu de nível!` | Tela de vitória. | ✅ Validado |
| `0x08071658` | `{PARTNER} Level Up!` | `{PARTNER} subiu de nível!` | Tela de vitória (Fera Guardiã). | ✅ Validado |
| `0x080716A0` | `Item Retrieval` | `Itens Obtidos` | Caixa de coleta de itens. | ✅ Validado |
| `0x080716C0` | `Weapon Retrieval` | `Armas Obtidas` | Caixa de coleta de armas/fragmentos. | ✅ Validado |
| `0x080716E4` | `You have Ability Points remaining.` | `Você ainda tem Pontos de Habilidade.` | Aviso na distribuição de status ao subir de nível. | ✅ Validado |
| `0x0807172C` | `Allocate Ability Points` | `Distribuir Pontos de Habilidade` | Título da tela de pontos de status. | ✅ Validado |
| `0x0807175C` | `Learned {VAR_2}!` | `Aprendeu {VAR_2}!` | Nova habilidade/magia aprendida. | ✅ Validado |
| `0x08071774` | `Learned Additional Magic!` | `Aprendeu Magia Adicional!` | Slot extra de magia desbloqueado. | ✅ Validado |
| `0x080717A8` | `Learned {VAR_4}!` | `Aprendeu {VAR_4}!` | Habilidade aprendida (slot 4). | ✅ Validado |
| `0x080717C0` | `Game Clear Time` | `Tempo de Conclusão` | Tela de encerramento/recordes. | ✅ Validado |
| `0x080717E0` | `Best Time` | `Melhor Tempo` | Recorde de tempo. | ✅ Validado |
| `0x080717F4` | `Kuhyra Level Up!` | `Kuhyra subiu de nível!` | Subida de nível de Kuhyra. | ✅ Validado |

---

## 2. Modo Link (Multiplayer / Troca / Arena) (`0x08071864`–`0x08072160`)

| Endereço ROM | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :---: |
| `0x08071864` | `Change selection.` | `Mudar seleção.` | ✅ Validado |
| `0x08071888` | `Only one weapon can be equipped.` | `Apenas uma arma pode ser equipada.` | ✅ Validado |
| `0x080718CC` | `Please remove the magic.` | `Por favor, remova a magia.` | ✅ Validado |
| `0x08071900` | `Please unequip the item.` | `Por favor, desequipe o item.` | ✅ Validado |
| `0x08071934` | `Please equip a weapon.` | `Por favor, equipe uma arma.` | ✅ Validado |
| `0x08071964` | `There is no weapon.` | `Não há nenhuma arma.` | ✅ Validado |
| `0x0807198C` | `There is no item.` | `Não há nenhum item.` | ✅ Validado |
| `0x080719B0` | `Reward can't be selected.` | `Impossível selecionar a recompensa.` | ✅ Validado |
| `0x080719E4` | `Start!` | `Começar!` | ✅ Validado |
| `0x080719F4` | `Now saving. Do not turn power off.` | `Salvando. Não feche o jogo.` | ✅ Validado |
| `0x08071A3C` | `Now loading. Do not turn power off.` | `Carregando. Não feche o jogo.` | ✅ Validado |
| `0x08071A88` | `Receive` | `Receber` | ✅ Validado |
| `0x08071A98` | `Send` | `Enviar` | ✅ Validado |
| `0x08071AA4` / `0x08072B5C` | `No` | `Não` | ✅ Validado |
| `0x08071AAC` / `0x08072B64` | `Yes` | `Sim` | ✅ Validado |
| `0x08071AB4` / `0x08072870` | `Is this okay?` | `Confirmar?` | ✅ Validado |
| `0x08071AD0` | `Trade the item?` | `Trocar o item?` | ✅ Validado |
| `0x08071AF0` | `Item trade is complete!` | `Troca de item concluída!` | ✅ Validado |
| `0x08071B20` | `Send the item.` | `Enviar o item.` | ✅ Validado |
| `0x08071B40` | `Display the Weapon List.` | `Exibir a Lista de Armas.` | ✅ Validado |
| `0x08071B74` | `Display the Item List.` | `Exibir a Lista de Itens.` | ✅ Validado |
| `0x08071BA4` | `Choose the reward.` | `Escolha a recompensa.` | ✅ Validado |
| `0x08071C88` | `Select rival character` | `Selecionar personagem rival` | ✅ Validado |
| `0x08071CB8` | `Select Summon Beast` | `Selecionar Summon Beast` | ✅ Validado |
| `0x08071CE0` | `Select main character` | `Selecionar personagem principal` | ✅ Validado |
| `0x08071D0C` | `Quit Link Mode` | `Sair do Modo Link` | ✅ Validado |
| `0x08071D2C` | `Play a match` | `Jogar uma partida` | ✅ Validado |
| `0x08071D48` | `Change equipment` | `Mudar equipamento` | ✅ Validado |
| `0x08071D6C` | `Change character` | `Mudar personagem` | ✅ Validado |
| `0x08071D90` | `Return to previous screen.` | `Voltar à tela anterior.` | ✅ Validado |
| `0x08071DC8` | `Move to next screen.` | `Avançar para a próxima tela.` | ✅ Validado |
| `0x08071DF4` | `Don't set up battle rewards.` | `Não definir recompensas de batalha.` | ✅ Validado |
| `0x08071E30` | `Set up battle rewards.` | `Definir recompensas de batalha.` | ✅ Validado |
| `0x08071E60` | `Items can't be used.` | `Itens não podem ser usados.` | ✅ Validado |
| `0x08071E8C` | `Items can be used.` | `Itens podem ser usados.` | ✅ Validado |
| `0x08071EB4` | `Magic can't be used.` | `Magias não podem ser usadas.` | ✅ Validado |
| `0x08071EE0` | `Magic can be used.` | `Magias podem ser usadas.` | ✅ Validado |
| `0x0807202C` | `Battle with Normal Rules` | `Batalha com Regras Normais` | ✅ Validado |
| `0x08072060` | `Battle with Tournament Rules` | `Batalha com Regras de Torneio` | ✅ Validado |
| `0x0807209C` | `Disconnect link` | `Desconectar Link` | ✅ Validado |
| `0x080720BC` | `Trade items/weapons` | `Trocar itens/armas` | ✅ Validado |
| `0x080720E4` | `Battle against a linked player.` | `Batalhar contra jogador conectado.` | ✅ Validado |
| `0x08072124` | `Press START for title screen.` | `Aperte START para a tela inicial.` | ✅ Validado |
| `0x08072160` | `Now linking. Do not turn power off.` | `Conectando. Não desligue.` | ✅ Validado |

---

## 3. Oficina de Forja e Categorias de Armas (`0x080721AC`–`0x08072408`)

| Endereço ROM | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :---: |
| `0x080721AC` | `Create weapons  ` | `Criar armas    ` | ✅ Validado |
| `0x080721D0` | `Create materials` | `Criar materiais` | ✅ Validado |
| `0x080721F4` / `0x080734D4` | `Drill Type` | `Drill Type` | ✅ Validado |
| `0x0807220C` / `0x080734EC` | `Knuckle Type` | `Knuckle Type` | ✅ Validado |
| `0x08072228` / `0x08073508` | `Spear Type` | `Spear Type` | ✅ Validado |
| `0x08072240` / `0x08073520` | `Axe Type` | `Axe Type` | ✅ Validado |
| `0x08072254` / `0x08073534` | `Sword Type` | `Sword Type` | ✅ Validado |
| `0x0807226C` | `{COLOR_1}Drill Type{COLOR_0}` | `{COLOR_1}Drill Type{COLOR_0}` | ✅ Validado |
| `0x08072288` | `{COLOR_1}Knuckle Type{COLOR_0}` | `{COLOR_1}Knuckle Type{COLOR_0}` | ✅ Validado |
| `0x080722A8` | `{COLOR_1}Spear Type{COLOR_0}` | `{COLOR_1}Spear Type{COLOR_0}` | ✅ Validado |
| `0x080722C4` | `{COLOR_1}Axe Type{COLOR_0}` | `{COLOR_1}Axe Type{COLOR_0}` | ✅ Validado |
| `0x080722DC` | `{COLOR_1}Sword Type{COLOR_0}` | `{COLOR_1}Sword Type{COLOR_0}` | ✅ Validado |
| `0x080722F8` / `0x08073578` | `Weapon` | `Arma` | ✅ Validado |
| `0x08072308` / `0x080735CC` | `Item  ` | `Item  ` | ✅ Validado |
| `0x08072318` | `Which one do you want?` | `Qual deles você quer?` | ✅ Validado |
| `0x08072348` / `0x080732A0` | `You have no techniques.` | `Você não possui técnicas.` | ✅ Validado |
| `0x08072378` / `0x08073328` | `You have no items.` | `Você não possui itens.` | ✅ Validado |
| `0x080723A0` / `0x080732FC` | `You have no weapons.` | `Você não possui armas.` | ✅ Validado |
| `0x080723CC` | `Which material will you use?` | `Qual material você vai usar?` | ✅ Validado |
| `0x08072408` | `Which weapon will you forge?` | `Qual arma você vai forjar?` | ✅ Validado |

---

## 4. Sistema de Save, Lojas e Menu de Pausa (`0x080726D8`–`0x08073ADC`)

| Endereço ROM | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :---: |
| `0x080726D8` | `Back  OK  ` | `Voltar OK ` | ✅ Validado |
| `0x08072944` | `deleted upon resuming game.` | `apagados ao retomar o jogo.` | ✅ Validado |
| `0x0807297C` | `Suspended save data will be` | `Os dados salvos suspensos serão` | ✅ Validado |
| `0x080729B4` | `There is no data.` | `Não há dados salvos.` | ✅ Validado |
| `0x080729D8` | `Do not turn power off.` | `Não feche o jogo.` | ✅ Validado |
| `0x08072A08` / `0x08073380` | `Failed to write data.` | `Falha ao salvar os dados.` | ✅ Validado |
| `0x08072A34` / `0x080733AC` | `Failed to read data.` | `Falha ao ler os dados.` | ✅ Validado |
| `0x08072A60` | `Version number does not match.` | `O número da versão não coincide.` | ✅ Validado |
| `0x08072AA0` | `Save data is corrupted.` | `Os dados salvos estão corrompidos.` | ✅ Validado |
| `0x08072AD0` | `New Data` | `Novo Jogo` | ✅ Validado |
| `0x08072AE4` | `Overwrite the data?` | `Sobrescrever os dados?` | ✅ Validado |
| `0x08072B0C` | `Load data?` | `Carregar dados?` | ✅ Validado |
| `0x08072B24` | `Delete data?` | `Apagar dados?` | ✅ Validado |
| `0x08072B40` | `Resume game?` | `Retomar o jogo?` | ✅ Validado |
| `0x08072B80` | `There's nothing left to sell.` | `Não há nada para vender.` | ✅ Validado |
| `0x08072BBC` / `0x080738DC` | `There are no more items.` | `Não há mais itens.` | ✅ Validado |
| `0x08072BF0` | `You can't carry any more of this.` | `Você não pode carregar mais disto.` | ✅ Validado |
| `0x08072C34` | `You don't have enough money.` | `Você não tem dinheiro suficiente.` | ✅ Validado |
| `0x08072C70` | `Sell` | `Vender` | ✅ Validado |
| `0x08072C7C` | `Buy ` | `Comprar` | ✅ Validado |
| `0x08073180` | `Equipment can't be changed.` | `O equipamento não pode ser trocado.` | ✅ Validado |
| `0x080731B8` / `0x0807374C` | `New technique` | `Nova técnica` | ✅ Validado |
| `0x080731D4` | ` paid` | ` pagos` | ✅ Validado |
| `0x080731E0` | ` sent` | ` enviados` | ✅ Validado |
| `0x08073220` | `You can't carry any more.` | `Você não pode carregar mais nada.` | ✅ Validado |
| `0x08073254` | ` received!` | ` recebido!` | ✅ Validado |
| `0x0807326C` | `You have no event items.` | `Você não tem itens chave.` | ✅ Validado |
| `0x08073350` | `Return to title screen.` | `Voltar para a tela inicial.` | ✅ Validado |
| `0x080733D8` | `Save game and quit?` | `Salvar o jogo e sair?` | ✅ Validado |
| `0x08073400` | `Overwrite previous save data?` | `Sobrescrever o jogo salvo anterior?` | ✅ Validado |
| `0x08073484` | `Bestiary` | `Bestiário` | ✅ Validado |
| `0x0807354C` | `Event Item` | `Item Chave` | ✅ Validado |
| `0x08073564` | `Technique` | `Técnica` | ✅ Validado |
| `0x08073588` | `Suspend Game` | `Suspender Jogo` | ✅ Validado |
| `0x080735A4` | `List` | `Lista` | ✅ Validado |
| `0x080735B0` | `Status` | `Status` | ✅ Validado |
| `0x080735C0` / `0x0807365C` | `Magic` | `Magia` | ✅ Validado |
| `0x080735D8` | `Support` | `Suporte` | ✅ Validado |
| `0x080735E8` | `Equipment` | `Equipamento` | ✅ Validado |
| `0x08073668` | `Remove` | `Remover` | ✅ Validado |
| `0x08073678` | `Equip` | `Equipar` | ✅ Validado |
| `0x08073684` | `Can't change equipment` | `Impossível mudar equip.` | ✅ Validado |
| `0x08073708` | `Use this Magic?` | `Usar esta Magia?` | ✅ Validado |
| `0x08073768` | `No more can be made.` | `Não é possível forjar mais.` | ✅ Validado |
| `0x08073794` | `Can't be used.` | `Não pode ser usado.` | ✅ Validado |
| `0x080737B4` | `This can't be used here.` | `Não pode ser usado aqui.` | ✅ Validado |
| `0x080737E8` | `You don't have enough materials.` | `Você não tem materiais suficientes.` | ✅ Validado |
| `0x0807382C` | `Mystic Ore` | `Mystic Ore` | ✅ Validado |
| `0x08073844` / `0x08073864` | `Use this item?` | `Usar este item?` | ✅ Validado |
| `0x08073884` | `Throw away` | `Descartar` | ✅ Validado |
| `0x0807389C` | `Use` | `Usar` | ✅ Validado |
| `0x080738A4` | `There are no more weapons.` | `Não há mais armas.` | ✅ Validado |
| `0x08073938` | `Keep forging?` | `Continuar forjando?` | ✅ Validado |
| `0x08073954` | `Toss how many` | `Descartar quantos?` | ✅ Validado |
| `0x08073970` | `Use how many` | `Usar quantos?` | ✅ Validado |
| `0x0807398C` | `Quit forging?` | `Parar de forjar?` | ✅ Validado |
| `0x08073A68` | `{VAR_2} wore off.` | `O efeito de {VAR_2} passou.` | ✅ Validado |
| `0x08073A90` | `Save the game?` | `Salvar o jogo?` | ✅ Validado |
| `0x08073AB0` | `HP and MP recovered.` | `HP e MP recuperados.` | ✅ Validado |
| `0x08073ADC` | `Use the teleporter?` | `Usar o teleportador?` | ✅ Validado |
| `0x081DD5AC` | `YES` | `SIM` | ✅ Validado |
| `0x081DD5B4` | `N O` | `NÃO` | ✅ Validado |


---

## 5. Telas Iniciais, Confirmação de Nome, Locais de Save e Modo Link (`0x08071AF0` – `0x08073C8C`)

| Endereço ROM | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :---: |
| `0x08072870` | `Is this okay?` | `Está bom assim?` | ✅ Validado |
| `0x0807288C` | `Big Bro` | `Mano` | ✅ Validado |
| `0x0807289C` | `Big Sis` | `Mana` | ✅ Validado |
| `0x08072B5C` / `0x08073210` / `0x08073A80` | `No` | `Não` | ✅ Validado |
| `0x08072B64` / `0x08073218` / `0x08073A88` | `Yes` | `Sim` | ✅ Validado |
| `0x0807343C` | `Now saving. Do not turn power off.` | `Salvando. Não desligue o jogo.` | ✅ Validado |
| `0x08073910` | `Is this okay` | `Está bom assim` | ✅ Validado |
| `0x08071AF0` | `Item trade is complete!` | `Troca de item concluída!` | ✅ Validado |
| `0x08071B20` | `Send the item.` | `Enviar o item.` | ✅ Validado |
| `0x08071B40` | `Display the Weapon List.` | `Exibir a Lista de Armas.` | ✅ Validado |
| `0x08071B74` | `Display the Item List.` | `Exibir a Lista de Itens.` | ✅ Validado |
| `0x08071BA4` | `Choose the reward.` | `Escolha a recompensa.` | ✅ Validado |
| `0x08071BCC` | `Deigleya Soldier` | `Soldado Deigleya` | ✅ Validado |
| `0x08071C88` | `Select rival character` | `Escolher rival` | ✅ Validado |
| `0x08071CB8` | `Select Summon Beast` | `Escolher Guardian Beast` | ✅ Validado |
| `0x08071CE0` | `Select main character` | `Escolher protagonista` | ✅ Validado |
| `0x08071D0C` | `Quit Link Mode` | `Sair do Modo Link` | ✅ Validado |
| `0x08071D2C` | `Play a match` | `Jogar partida` | ✅ Validado |
| `0x08071D48` | `Change equipment` | `Mudar equipamento` | ✅ Validado |
| `0x08071D6C` | `Change character` | `Mudar personagem` | ✅ Validado |
| `0x08071D90` | `Return to previous screen.` | `Voltar para a tela anterior.` | ✅ Validado |
| `0x08071DC8` | `Move to next screen.` | `Ir para a próxima tela.` | ✅ Validado |
| `0x08071DF4` | `Don't set up battle rewards.` | `Não definir recompensas.` | ✅ Validado |
| `0x08071E30` | `Set up battle rewards.` | `Definir recompensas de luta.` | ✅ Validado |
| `0x08071E60` | `Items can't be used.` | `Itens não podem ser usados.` | ✅ Validado |
| `0x08071E8C` | `Items can be used.` | `Itens podem ser usados.` | ✅ Validado |
| `0x08071EB4` / `0x080732D0` | `Magic can't be used.` | `Magia não pode ser usada.` | ✅ Validado |
| `0x08071EE0` | `Magic can be used.` | `Magia pode ser usada.` | ✅ Validado |
| `0x08071F08` | `Labyrinth 2` | `Labirinto 2` | ✅ Validado |
| `0x08071F20` | `Fort Mirana Docks` | `Docas do Forte Mirana` | ✅ Validado |
| `0x08071F44` / `0x08072D44` | `Fort Mirana` | `Forte Mirana` | ✅ Validado |
| `0x08071F5C` | `Lighthouse Rooftop` | `Topo do Farol` | ✅ Validado |
| `0x08071F84` / `0x08072D5C` | `Cape Lighthouse` | `Farol do Cabo` | ✅ Validado |
| `0x08071FA4` / `0x08072D7C` | `Marine Dungeon` | `Calabouço Marinho` | ✅ Validado |
| `0x08071FC4` / `0x08072EE4` | `Upper Wystern` | `Wystern Alta` | ✅ Validado |
| `0x08071FE0` / `0x08072F20` | `Lower Wystern` | `Wystern Baixa` | ✅ Validado |
| `0x08071FFC` / `0x08072D9C` | `Labyrinth` | `Labirinto` | ✅ Validado |
| `0x08072010` | `Battle Arena` | `Arena de Batalha` | ✅ Validado |
| `0x08072D14` | `Ship Workshop` | `Oficina do Navio` | ✅ Validado |
| `0x08072D30` | `Ship Helm` | `Leme do Navio` | ✅ Validado |
| `0x08072DC0` | `Vance Cape` | `Cabo Vance` | ✅ Validado |
| `0x08072DD8` | `Kagro Volcano` | `Vulcão Kagro` | ✅ Validado |
| `0x08072DF4` | `Rugista Island` | `Ilha Rugista` | ✅ Validado |
| `0x08072E14` | `Central Tower 4F` | `Torre Central 4A` | ✅ Validado |
| `0x08072E38` | `Central Tower 3F` | `Torre Central 3A` | ✅ Validado |
| `0x08072E5C` | `Central Tower 2F` | `Torre Central 2A` | ✅ Validado |
| `0x08072E80` | `Central Tower 1F` | `Torre Central 1A` | ✅ Validado |
| `0x08072EA4` | `Silver Guild 2F` | `Guilda Prateada 2A` | ✅ Validado |
| `0x08072EC4` | `Silver Guild 1F` | `Guilda Prateada 1A` | ✅ Validado |
| `0x08072F00` | `Middle Wystern` | `Wystern Central` | ✅ Validado |
| `0x08072F48` | `Rumari's House` | `Casa da Rumari` | ✅ Validado |
| `0x08072F68` | `Hideout` | `Esconderijo` | ✅ Validado |
| `0x08072F78` | `Mayor's House` | `Casa do Prefeito` | ✅ Validado |
| `0x08072F94` | `Hidden Room` | `Sala Secreta` | ✅ Validado |
| `0x08072FAC` | `Assembly Hall` | `Salão de Assembleia` | ✅ Validado |
| `0x08072FC8` | `Arena` | `Arena` | ✅ Validado |
| `0x08072FD4` | `Workshop` | `Oficina` | ✅ Validado |
| `0x08072FE8` | `Trish Workshop` | `Oficina da Trish` | ✅ Validado |
| `0x08073008` | `Cazio Workshop` | `Oficina do Cazio` | ✅ Validado |
| `0x08073028` | `Ariel/Mariel Lab` | `Lab. Ariel/Mariel` | ✅ Validado |
| `0x0807304C` | `Razzy Workshop` | `Oficina da Razzy` | ✅ Validado |
| `0x0807306C` | `Sanary Workshop` | `Oficina da Sanary` | ✅ Validado |
| `0x0807308C` | `My Workshop` | `Minha Oficina` | ✅ Validado |
| `0x080730A4` | `Rondeau's House` | `Casa do Rondeau` | ✅ Validado |
| `0x080730C4` | `Gold Guild` | `Guilda Dourada` | ✅ Validado |
| `0x080730DC` | `Sakuro's House` | `Casa do Sakuro` | ✅ Validado |
| `0x080730FC` | `Port` | `Porto` | ✅ Validado |
| `0x08073108` | `House` | `Casa` | ✅ Validado |
| `0x08073114` | `Inn` | `Pousada` | ✅ Validado |
| `0x0807311C` | `Weapon Shop` | `Loja de Armas` | ✅ Validado |
| `0x08073134` | `Item Shop` | `Loja de Itens` | ✅ Validado |
| `0x08073148` | `Home` | `Minha Casa` | ✅ Validado |
| `0x08073B04` | `Labyrinth  1F` | `Labirinto  1A` | ✅ Validado |
| `0x08073B20` | `Labyrinth  3F` | `Labirinto  3A` | ✅ Validado |
| `0x08073B3C` | `Labyrinth  6F` | `Labirinto  6A` | ✅ Validado |
| `0x08073B58` | `Labyrinth 11F` | `Labirinto 11A` | ✅ Validado |
| `0x08073B74` | `Labyrinth 18F` | `Labirinto 18A` | ✅ Validado |
| `0x08073B90` | `Labyrinth 26F` | `Labirinto 26A` | ✅ Validado |
| `0x08073BAC` | `Labyrinth 31F` | `Labirinto 31A` | ✅ Validado |
| `0x08073BC8` | `Labyrinth 37F` | `Labirinto 37A` | ✅ Validado |
| `0x08073BE4` | `Labyrinth 45F` | `Labirinto 45A` | ✅ Validado |
| `0x08073C00` | `Labyrinth 50F` | `Labirinto 50A` | ✅ Validado |
| `0x08073C1C` | `Labyrinth 56F` | `Labirinto 56A` | ✅ Validado |
| `0x08073C38` | `Labyrinth 66F` | `Labirinto 66A` | ✅ Validado |
| `0x08073C54` | `Labyrinth 76F` | `Labirinto 76A` | ✅ Validado |
| `0x08073C70` | `Labyrinth 86F` | `Labirinto 86A` | ✅ Validado |
| `0x08073C8C` | `Labyrinth 96F` | `Labirinto 96A` | ✅ Validado |
