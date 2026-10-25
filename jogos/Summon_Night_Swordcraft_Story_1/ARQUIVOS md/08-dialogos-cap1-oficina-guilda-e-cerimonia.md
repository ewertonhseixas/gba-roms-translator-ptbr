# 08 — Diálogos do Jogo (Parte 1): Oficina, Guilda Prateada, Wystern e Cerimônia de Abertura

Este documento apresenta os diálogos extraídos dos **Scripts de Eventos PSI3 (`#0101` a `#0262`)** do Archive #2 (`0x085C10DC`).
Para facilitar a sua leitura e validação, **agrupamos as linhas consecutivas de uma mesma caixa de diálogo** (indicando o intervalo de offsets dentro do script descomprimido) e colocamos ao lado a **tradução sugerida em Português (PT-BR)** mantendo o tom, o humor e a personalidade de cada personagem.

---

## 1. Script `#0101` (`0x085CA55C`) — Baús e Portas do Labirinto

| Offset (PSI3) | Opcode | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x0216` | `0x021D` | `Small Key used!` | `Chave Pequena usada!` | ✅ Validado |
| `+0x0262` | `0x0218` | `It opened...` | `Abriu...` | ✅ Validado |
| `+0x02F2` | `0x0218` | `It's empty...` | `Está vazio...` | ✅ Validado |

---

## 2. Script `#0170` (`0x085CE53C`) — Mestre Bron: Aprendizado de Técnicas na Forja

| Offset (PSI3) | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x058E`–`0x0612` | **Mestre Bron** | `Whoa, not so fast! Go forge that`<br>`last weapon I taught ya before`<br>`moving on to the next!` | `Opa, não tão rápido! Vá forjar`<br>`aquela última arma que te ensinei`<br>`antes de passar para a próxima!` | ✅ Validado |
| `+0x0684`–`0x06C8` | **Mestre Bron** | `There ain't any techniques I can`<br>`teach ya right now.` | `Não há nenhuma técnica que eu`<br>`possa te ensinar agora.` | ✅ Validado |
| `+0x0746` | **Mestre Bron** | `Hm? You're gonna quit?` | `Hm? Já vai desistir?` | ✅ Validado |
| `+0x07FE`–`0x083C` | **Protagonista** | `I gotta forge the last weapon`<br>`first...` | `Preciso forjar a última arma`<br>`primeiro...` | ✅ Validado |
| `+0x0890`–`0x08CE` | **Protagonista** | `I guess there aren't any more`<br>`techniques I can forge.` | `Acho que não há mais nenhuma`<br>`técnica que eu possa forjar.` | ✅ Validado |
| `+0x0954` | **Escolha** | `Never mind.` | `Deixa pra lá.` | ✅ Validado |

---

## 3. Script `#0201` (`0x085CF45C`) — Chegada à Nova Oficina (Variações por Guardiã)

> [!NOTE]
> Este script mostra como o jogo armazena as reações das 4 Guardiãs (**Rasho**, **Sanary**, **Sugar** e **Kutty**) para a mesma cena quando o protagonista ganha sua própria oficina no 2º andar da Guilda Prateada.

| Offset (PSI3) | Personagem | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x0160`–`0x0190` | **Protagonista** | `Let's go upstairs now.`<br>`Master will be waiting for us.` | `Vamos subir agora.`<br>`O Mestre deve estar nos esperando.` | ✅ Validado |
| `+0x01D6`–`0x0206` | **Protagonista** | `Let's go upstairs now.`<br>`Master Bron is waiting for us.` | `Vamos subir agora.`<br>`O Mestre Bron está nos esperando.` | ✅ Validado |
| `+0x0322`–`0x0358` | **Protagonista (c/ Rasho)** | `Soon, we're going to have`<br>`our own workshop!` | `Em breve, nós vamos ter`<br>`a nossa própria oficina!` | ✅ Validado |
| `+0x0384`–`0x03B8` | **Protagonista (c/ Sanary)** | `Soon, we'll get our very`<br>`own workshop!` | `Logo nós vamos ganhar`<br>`uma oficina só nossa!` | ✅ Validado |
| `+0x042E`–`0x0464` | **Rasho** | `And, eventually, it'll be`<br>`my own room.` | `E, com o tempo, vai virar`<br>`o meu próprio quarto.` | ✅ Validado |
| `+0x04EA` | **Sanary** | `It's my workshop!` | `É a minha oficina!` | ✅ Validado |
| `+0x0520` | **Protagonista** | `It's my workshop!` | `É a *minha* oficina!` | ✅ Validado |
| `+0x059E`–`0x05DC` | **Sugar** | `This workshop is for just the`<br>`two of us! Isn't that romantic?` | `Esta oficina é só para nós!`<br>`Não é romântico?` | ✅ Validado |
| `+0x066E` | **Protagonista** | `Yeah! Wait... what!?` | `É! Espera... o quê!?` | ✅ Validado |
| `+0x06EC` | **Kutty** | `Kutty!` | `Kutty!` | ✅ Validado |
| `+0x075C`–`0x079A` | **Protagonista (c/ Kutty)** | `Our own workshop will soon be`<br>`ready! That'll be nice, huh?` | `Nossa oficina vai ficar pronta`<br>`logo! Vai ser ótimo, não é?` | ✅ Validado |
| `+0x07DC`–`0x0820` | **Protagonista (Alt)** | `Our own workshop is almost done!`<br>`Won't that be nice?` | `Nossa oficina está quase pronta!`<br>`Não vai ser legal?` | ✅ Validado |

---

## 4. Scripts `#0202` e `#0203` (`0x085CF78C` / `0x085CFC7C`) — Quarto do Protagonista: Ingresso e Scooter Aquática

| Offset (PSI3) | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x0452`–`0x04DC` | **Amariss (Mãe)** | `If you have everything you need,`<br>`get going! You don't want to miss`<br>`the opening ceremony!` | `Se já pegou tudo o que precisa,`<br>`vá andando! Você não vai querer`<br>`perder a cerimônia de abertura!` | ✅ Validado |
| `+0x0584`–`0x05B6` | **Amariss** | `Off to the Silver Guild`<br>`with you! Chop-chop!` | `Direto para a Guilda Prateada!`<br>`Vamos, rapidinho!` | ✅ Validado |
| `+0x060A` | **Sistema** | `Got Water Scooter!` | `Obteve a Moto Aquática!` | ✅ Validado |
| `+0x0640`–`0x0678` | **Protagonista** | `(This is my Water Scooter!`<br>`With it, I can ride across water.)` | `(Esta é minha Moto Aquática!`<br>`Com ela, posso navegar pela água.)` | ✅ Validado |
| `+0x0A5A`–`0x0ADE` | **Amariss** | `Do you have the Entrance Ticket?`<br>`You won't be able to enter the`<br>`tournament without it!` | `Você pegou o Ingresso de Entrada?`<br>`Não vai conseguir entrar no`<br>`torneio sem ele!` | ✅ Validado |
| `+0x0B4A`–`0x0B82` | **Protagonista** | `Oh! I forgot all about it!`<br>`It should be in my dresser.` | `Ah! Esqueci completamente dele!`<br>`Deve estar na minha cômoda.` | ✅ Validado |
| `+0x0BFA`–`0x0C84` | **Amariss** | `Don't forget your Water Scooter!`<br>`You'll never reach the tournament`<br>`in time if you have to swim there!` | `Não esqueça a sua Moto Aquática!`<br>`Você nunca vai chegar ao torneio`<br>`a tempo se tiver que ir nadando!` | ✅ Validado |
| `#0203 +0x01F0` | **Protagonista** | `(This is my Entrance Ticket!`<br>`I can't get into the Central`<br>`Tower without it.)` | `(Este é meu Ingresso de Entrada!`<br>`Não posso entrar na Torre`<br>`Central sem ele.)` | ✅ Validado |

---

## 5. Script `#0204` (`0x085CFECC`) — Exteriores de Wystern e Entrada da Guilda Prateada

| Offset (PSI3) | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x091E`–`0x09CC` | **Protagonista** | `(The Central Tower.)`<br>`(It's in the heart of the city,`<br>`but I've never been inside.)`<br>`(I wonder what it looks like...?)` | `(A Torre Central.)`<br>`(Fica no coração da cidade,`<br>`mas eu nunca entrei lá.)`<br>`(Como será por dentro...?)` | ✅ Validado |
| `+0x0A42`–`0x0B58` | **Recepcionista da Guilda** | `Welcome to the Silver Guild,`<br>`fair citizen of Wystern...`<br>`...Oh, it's you, {PLAYER}.`<br>`The tournament starts today,`<br>`doesn't it? Do your best, and`<br>`make us proud!` | `Bem-vindo à Guilda Prateada,`<br>`nobre cidadão de Wystern...`<br>`...Ah, é você, {PLAYER}.`<br>`O torneio começa hoje,`<br>`não é? Dê o seu melhor e`<br>`nos dê orgulho!` | ✅ Validado |
| `+0x0B98`–`0x0C1A` | **Visitante** | `Now I understand why Wystern`<br>`is the City of Swords. This place`<br>`is teeming with Craftknights!` | `Agora entendo por que Wystern`<br>`é a Cidade das Espadas. Este`<br>`lugar está cheio de`<br>`Cavaleiros!` | ✅ Validado |
| `+0x0C78` | **Guarda** | `The door behind me leads upstairs.` | `A porta atrás leva lá pra cima.` | ✅ Validado |
| `+0x0CE0`–`0x0E12` | **Morador** | `Hey, {PLAYER}.`<br>`The Central Tower is at the end`<br>`of this path... but you know that.`<br>`You'd better get to the opening`<br>`ceremony. I'd be surprised if it`<br>`hasn't already started!` | `Ei, {PLAYER}.`<br>`A Torre Central fica no fim`<br>`deste caminho… você já sabe.`<br>`Melhor ir logo pra cerimônia!`<br>`Ficaria surpreso se ela`<br>`já não tiver começado!` | ✅ Validado |
| `+0x0E68`–`0x0EEC` | **Cidadão Curioso** | `Wystern is located atop a huge`<br>`tower in the sea... so why hasn't`<br>`it sunk or floated away yet?` | `Wystern fica no topo de uma enorme`<br>`torre no mar… por que será que`<br>`ainda não afundou nem boiou longe?` | ✅ Validado |
| `+0x0F48`–`0x0FC0` | **Idoso** | `I wish I was young enough to`<br>`enter the tournament... or to`<br>`remember my own name...` | `Queria ser jovem o bastante para`<br>`entrar no torneio... ou para`<br>`lembrar do meu próprio nome...` | ✅ Validado |
| `+0x1010`–`0x108A` | **Jovem** | `A Craftlord is much more`<br>`than a mere blacksmith. He's also`<br>`a heroic knight of Wystern!` | `Um Lorde é bem mais`<br>`que um simples ferreiro. Ele é um`<br>`cavaleiro heroico de Wystern!` | ✅ Validado |
| `+0x10E4` | **Garoto** | `I'm gonna be a Craftknight!` | `Eu serei um Cavaleiro!` | ✅ Validado |
| `+0x113E`–`0x11C6` | **Garota** | `Master Kouren is beautiful and`<br>`strong! I want to be just like her`<br>`when I grow up!` | `A Mestra Kouren é linda e`<br>`forte! Quero ser igualzinha a ela`<br>`quando eu crescer!` | ✅ Validado |
| `+0x1290`–`0x12C0` | **Gato** | `Meow.` / `Meow!` | `Miau. / Miau!` | ✅ Validado |

---

## 6. Scripts `#0208` e `#0211` (`0x085D093C` / `0x085D0F2C`) — Interior da Guilda Prateada (1º e 2º Andar)

| Offset (PSI3) | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `#0208 +0x0566`–`0x06A4` | **Protagonista** | `I have to see Master Bron.`<br>`I think he went upstairs...` | `Preciso ver o Mestre Bron.`<br>`Acho que ele subiu as escadas...` | ✅ Validado |
| `#0208 +0x0952`–`0x0966` | **Aprendiz** | `Hmm...`<br>`Uh... can I leave now?` | `Hmm...`<br>`Ér... já posso ir embora?` | ✅ Validado |
| `#0208 +0x09BC`–`0x0AD6` | **Membro da Guilda** | `Master Bron is up on the second`<br>`floor.`<br>`He told me he was preparing a`<br>`workshop for you and the other`<br>`tournament entrants.` | `O Mestre Bron está lá no segundo`<br>`andar.`<br>`Ele me disse que estava preparando`<br>`uma oficina para você e os outros`<br>`participantes do torneio.` | ✅ Validado |
| `#0208 +0x0B32`–`0x0B72` | **Ferreiro** | `I'll be watching your matches.`<br>`Good luck!` | `Vou assistir às suas lutas.`<br>`Boa sorte!` | ✅ Validado |
| `#0208 +0x0BA0` | **Moça** | `What a cute Guardian Beast!` | `Que Guardiã mais fofinha!` | ✅ Validado |
| `#0208 +0x0C18` | **Rasho / Sanary** | `Did you say I'm cute?` | `Você me chamou de fofinha?` | ✅ Validado |
| `#0208 +0x0C70`–`0x0C98` | **Ferreiro** | `What am I supposed`<br>`to make today?` | `O que será que eu devo`<br>`forjar hoje?` | ✅ Validado |
| `#0211 +0x0352`–`0x0412` | **Mestre Bron** | `Here you are!`<br>`Only tournament entrants are`<br>`allowed into the workshop on`<br>`the second floor.`<br>`And your workshop is here.` | `Aí está você!`<br>`Apenas participantes do torneio têm`<br>`permissão para usar a oficina do`<br>`segundo andar.`<br>`E a sua oficina fica bem aqui.` | ✅ Validado |
| `#0211 +0x0496` / `04B8` | **Protagonista** | `Yes, Master.` / `Alright.` | `Sim, Mestre. / Certo.` | ✅ Validado |
| `#0211 +0x0554`–`0x0576` | **Mestre Bron** | `It's not there.`<br>`It's here, {PLAYER}!` | `Não é aí.`<br>`É aqui, {PLAYER}!` | ✅ Validado |

---

## 7. Scripts `#0214`, `#0215`, `#0217`, `#0220` e `#0221` — Loja de Itens e Torre Central (Cerimônia de Abertura)

| Script / Offset | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `#0214 +0x0254`–`0x0356` | **Cliente na Loja** | `I came to pick up some items,`<br>`but nobody is here!`<br>`The shopkeeper recently sold out`<br>`of weapon-making materials, but`<br>`he'll be restocked soon.` | `Vim buscar alguns itens,`<br>`mas não tem ninguém aqui!`<br>`O lojista vendeu todo o estoque`<br>`de materiais de forja há pouco, mas`<br>`vai repor as prateleiras em breve.` | ✅ Validado |
| `#0214 +0x039E`–`0x05BA` | **Aventureiro (Dica dos Barris)** | `If you find barrels or boxes in`<br>`the Labyrinth, break them open.`<br>`They contain extra items!`<br>`Well... they don't ALWAYS contain`<br>`extra items.`<br>`When you leave the Labyrinth and`<br>`then return, the barrels and boxes`<br>`you broke will be repaired.`<br>`Don't ask me how the heck`<br>`that works!` | `Se encontrar barris ou caixas no`<br>`Labirinto, quebre-os.`<br>`Eles contêm itens extras!`<br>`Bom... nem SEMPRE eles contêm`<br>`itens extras.`<br>`Quando você sai do Labirinto e`<br>`volta depois, os barris e caixas`<br>`que você quebrou estarão inteiros.`<br>`Não me pergunte como diabos`<br>`isso funciona!` | ✅ Validado |
| `#0215 +0x02D2`–`0x0322` | **Colega** | `Hey, {PLAYER}. `<br>`Why so down? Did Master Bron`<br>`tear you a new one again?` | `Ei, {PLAYER}.`<br>`Por que tão desanimado? O Bron`<br>`te deu outra bronca daquelas?` | ✅ Validado |
| `#0215 +0x03BC`–`0x075A` | **Sábio Curioso** | `Curiosity is the most important`<br>`of human desires.`<br>`When you try something,`<br>`you will experience something.`<br>`It might be good or bad, but`<br>`it will always be educational.`<br>`...`<br>`Do you burn with curiosity?`<br>`Do you want to experience a`<br>`variety of strange situations?`<br>`Then you must venture not`<br>`only where you are supposed`<br>`to go, but where you are not!` | `A curiosidade é o mais importante`<br>`dos desejos humanos.`<br>`Quando você tenta algo,`<br>`vivencia uma experiência.`<br>`Pode ser boa ou ruim, mas`<br>`será sempre um aprendizado.`<br>`...`<br>`Você arde de curiosidade?`<br>`Quer vivenciar uma variedade`<br>`de situações inusitadas?`<br>`Então deve se aventurar não`<br>`apenas onde deveria ir,`<br>`mas também onde não deveria!` | ✅ Validado |
| `#0217 +0x03CC`–`0x0454` | **Guerreiro Frustrado** | `Damn! If fighting skills were all`<br>`that mattered, I could become a`<br>`Craftlord in my sleep!` | `Droga! Se habilidade de luta fosse`<br>`tudo o que importasse, eu viraria`<br>`um Lorde de olhos fechados!` | ✅ Validado |
| `#0220 +0x0A26`–`0x0B0A` | **Recepcionista da Torre Central** | `Entrance Ticket, please.`<br>`You're {PLAYER}, yes?`<br>`The opening ceremony is`<br>`taking place in this hall.`<br>`Enter, please.` | `Seu ingresso, por favor.`<br>`Você é {PLAYER}, certo?`<br>`A cerimônia de abertura está`<br>`acontecendo neste salão.`<br>`Pode entrar, por favor.` | ✅ Validado |
| `#0221 +0x067C`–`0x0704` | **Rival no Salão** | `Are you sure that you're`<br>`ready to fight?`<br>`From this moment on,`<br>`we're enemies.` | `Tem certeza de que está`<br>`pronto para lutar?`<br>`Deste momento em diante,`<br>`somos inimigos.` | ✅ Validado |
| `#0221 +0x07B8`–`0x082E` | **Participante** | `The City of Swords is protected`<br>`by the seven Craftlords.`<br>`Or did you already know that?` | `A Cidade das Espadas é protegida`<br>`pelos sete Lordes.`<br>`Ou você já sabia disso?` | ✅ Validado |
| `#0221 +0x0976`–`0x0F72` | **Participante (Tutorial de Guardiã)** | `Hey, you!`<br>`Who's your Guardian Beast?`<br>*(Escolha 1)* `I haven't got one yet.`<br>*(Escolha 2)* `What's a Guardian Beast?`<br>`Everyone in the tournament will`<br>`use a weapon that was made with`<br>`the help of a Guardian Beast.`<br>`You'll never survive if you don't`<br>`have a Guardian Beast of your own!`<br>`A Guardian Beast is a creature`<br>`that acts as your assistant to`<br>`help you forge weapons.`<br>`...`<br>`You don't know!? It's a creature`<br>`that's summoned to our world`<br>`from another dimension!` | `Ei, você!`<br>`Quem é a sua Guardiã?`<br>`*(Escolha 1)* Ainda não tenho uma.`<br>`*(Escolha 2)* O que é uma Guardiã?`<br>`Todos no torneio vão usar`<br>`uma arma forjada com a`<br>`ajuda de uma Guardiã.`<br>`Você nunca vai sobreviver se não`<br>`tiver uma Guardiã própria!`<br>`Uma Guardiã é uma criatura`<br>`que atua como sua assistente para`<br>`ajudar você a forjar armas.`<br>`...`<br>`Você não sabe!? É uma criatura`<br>`invocada para o nosso mundo`<br>`vinda de outra dimensão!` | ✅ Validado |

---

## 8. Scripts `#0250`, `#0259`, `#0260`, `#0261` e `#0262` — Casas dos Moradores de Wystern (Humor e Lore)

| Script / Offset | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `#0250 +0x01F0`–`0x02B8` | **Dono de Casa** | `My wife works to pay the bills,`<br>`and I stay at home with the kids.`<br>`She definitely has the better`<br>`end of the deal...` | `Minha esposa paga as contas,`<br>`e eu fico em casa com as crianças.`<br>`Ela com certeza ficou com a`<br>`parte mais fácil do acordo…` | ✅ Validado |
| `#0250 +0x02E0`–`0x036E` | **Morador Desastrado** | `I'm too clumsy to be a Craftknight.`<br>`I'd probably forge a sword to my`<br>`shin...` | `Sou desastrado demais para ser`<br>`um forjador. Eu até forjaria uma`<br>`espada direto na minha canela…` | ✅ Validado |
| `#0259 +0x01DC`–`0x035C` | **Mãe do Viciado em Curry** | `My kid likes curry.`<br>`I mean, really likes curry.`<br>`Really, REALLY likes curry.`<br>`My child is completely addicted to`<br>`curry, so I want to help him break`<br>`the habit.`<br>`What would you call that?`<br>`Going cold curry?` *(trocadilho com "cold turkey")* | `Meu filho gosta de curry.`<br>`Quer dizer, gosta MUITO de curry.`<br>`Gosta MUITO, MUITO MESMO de curry.`<br>`Meu filho é vidrado em curry,`<br>`preciso ajudá-lo a largar`<br>`esse vício de uma vez.`<br>`Como é que se chama isso mesmo?`<br>`Abstinência de curry?` | ✅ Validado |
| `#0259 +0x0396`–`0x0416` | **Morador** | `Curry was a popular food in `<br>`another time and place. Now it's`<br>`the most popular food in Wystern!` | `O curry era um prato popular em`<br>`outro tempo e lugar. Agora é`<br>`a comida mais famosa de Wystern!` | ✅ Validado |
| `#0260 +0x055C`–`0x05CC` | **Senhora** | `Are you a cat person or a`<br>`dog person? You look like a`<br>`cat person to me.` | `Você prefere gatos ou`<br>`cachorros? Para mim, você tem`<br>`cara de quem gosta de gatos.` | ✅ Validado |
| `#0260 +0x0688`–`0x0708` | **Veterano** | `There are three generations of`<br>`Craftknights in my family, but`<br>`none of us became a Craftlord.` | `São três gerações de Cavaleiros`<br>`Forjadores na família, mas nenhum`<br>`de nós se tornou Lorde.` | ✅ Validado |
| `#0261 +0x02F0`–`0x036E` | **Cidadão Indignado** | `The opening ceremony is over?`<br>`Already? I was expecting it to`<br>`last until sundown! Rip-off!` | `A cerimônia de abertura já acabou?`<br>`Tão rápido? Eu esperava que durasse`<br>`até o pôr do sol! Que roubo!` | ✅ Validado |
| `#0262 +0x04FE`–`0x0624` | **Fã de Soqueiras** | `My dad says that the knuckle-type`<br>`is the best weapon, so it must be`<br>`true!`<br>`The knuckle-type is the only`<br>`weapon that a real man uses!`<br>`Just ask my father and brother!` | `Meu pai diz que a Soqueira`<br>`é a melhor arma de todas,`<br>`então deve ser verdade!`<br>`É a única arma de homem!`<br>`Pergunte pro meu pai ou pro irmão!` | ✅ Validado |