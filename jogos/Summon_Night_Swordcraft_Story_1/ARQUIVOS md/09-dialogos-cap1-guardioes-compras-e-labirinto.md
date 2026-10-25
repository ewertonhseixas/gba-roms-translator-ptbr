# 09 — Diálogos do Jogo (Parte 2): Guardiãs, Compras, 1º Labirinto e Tutorial de Minérios

Este documento reúne os diálogos dos **Scripts de Eventos PSI3 (`#0301` a `#0307`)** do Archive #2 (`0x085D3F9C`–`0x085D668C`).
Estes scripts são fundamentais para validar a localização porque contêm **as 4 variações de personalidade das Guardiãs (`Rasho`, `Sanary`, `Sugar` e `Kutty`)** interagindo com o protagonista (`{PLAYER}`), além do grande guia da cidade e do tutorial completo sobre **Minérios Místicos (*Mystic Ores*)** e **Invocações Errantes (*Stray Summons*)**.

---

## 1. Script `#0301` (`0x085D3F9C`) — Compras na Loja de Itens, Expedição ao Labirinto e Preparação para a 1ª Luta

### 1.1. Discussão sobre o Treinamento (Com Mestre Bron)
| Offset (PSI3) | Personagem | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x0148` | **Protagonista** | `Let's go see Master Bron!` | `Vamos ver o Mestre Bron!` | ✅ Validado |
| `+0x0286` | **Protagonista** | `Am I so unreliable?` | `Eu pareço tão pouco confiável?` | ✅ Validado |
| `+0x0304` | **Rasho** | `You really are a fledgling, dude...` | `Você é mesmo um novato, cara...` | ✅ Validado |
| `+0x039C`–`0x03AC` | **Protagonista** | `What!?`<br>`Well, then you teach me.` | `O quê!?`<br>`Bom, então me ensine você.` | ✅ Validado |
| `+0x0430`–`0x0462` | **Sanary** | `Why should I teach you?`<br>`Teaching isn't my thing!` | `Por que eu deveria te ensinar?`<br>`Ensinar não é a minha praia!` | ✅ Validado |
| `+0x04E6` | **Protagonista** | `You're selfish...` | `Você é tão egoísta...` | ✅ Validado |
| `+0x055E`–`0x0592` | **Sugar** | `If I may, I'll teach you`<br>`many things...♡` | `Se me permitir, eu lhe ensinarei`<br>`muitas coisas...♡` | ✅ Validado |
| `+0x0604`–`0x0618` | **Protagonista** | `Hahaha...`<br>`Thanks, but no thanks.` | `Hahaha...`<br>`Valeu, mas deixa quieto.` | ✅ Validado |
| `+0x069C`–`0x0716` | **Kutty & Protagonista** | `Kutty!`<br>`Alright, {PARTNER}.`<br>`Let's hurry!` | `Kutty!`<br>`Certo, {PARTNER}.`<br>`Vamos depressa!` | ✅ Validado |

### 1.2. Ida à Loja de Itens (Liquidação de Minério de Ferro!)
| Offset (PSI3) | Personagem | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x079E`–`0x07DE` | **Protagonista** | `Hurry! We must get to the Item`<br>`Shop! The iron ore will be sold out!` | `Depressa! Precisamos chegar à Loja`<br>`de Itens! O iron ore vai esgotar!` | ✅ Validado |
| `+0x0830`–`0x0870` | **Sanary / Sugar** | `Sale, sale, Iron Ore on sale♪`<br>`We're off to the Item Shop♪` | `Promoção, promoção de Iron Ore♪`<br>`Vamos para a Loja de Itens♪` | ✅ Validado |
| `+0x0988`–`0x09E6` | **Protagonista** | `Alright. `<br>`Let's finish our shopping quickly,`<br>`and make a weapon!` | `Certo.`<br>`Vamos terminar as compras rapidinho`<br>`e forjar uma arma!` | ✅ Validado |
| `+0x0A52`–`0x0AB6` | **Sanary** | `Don't you get it?`<br>`I love shopping! It's so fun!`<br>`Woohoo♪` | `Você não entende?`<br>`Adoro fazer compras! É divertido!`<br>`Uhuuu♪` | ✅ Validado |
| `+0x0B22`–`0x0B90` | **Rasho** | `Alright, alright.`<br>`Let's just get this shopping thing`<br>`over with.` | `Tá legal, tá legal.`<br>`Vamos logo acabar com essa`<br>`história de compras.` | ✅ Validado |
| `+0x0CBE`–`0x0D0E` | **Sanary** | `Okay, okay.`<br>`You can just wait outside`<br>`until I'm done.` | `Tá bom, tá bom.`<br>`Você pode ficar esperando lá fora`<br>`até eu terminar.` | ✅ Validado |
| `+0x0D88`–`0x0E86` | **Sugar** | `I'm always excited by sales!`<br>*(Protagonista:)* `Really?`<br>`Yes!`<br>`It gets my heart pumping!` | `Promoções sempre me deixam animada!`<br>`*(Protagonista:)* Sério?`<br>`Sim!`<br>`Faz meu coração bater mais forte!` | ✅ Validado |
| `+0x1012`–`0x104C` | **Protagonista** | `Are you psyched to make the`<br>`best buys? Okay, beat me if you can!` | `Pronto para conseguir as melhores`<br>`ofertas? Quem chega primeiro!?` | ✅ Validado |

### 1.3. Minério Esgotado e Rumo ao Labirinto
| Offset (PSI3) | Personagem | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x1108`–`0x1138` | **Protagonista** | `The iron ore sold out.`<br>`We need to go see Master Bron...` | `O iron ore esgotou.`<br>`Temos que voltar ao Mestre Bron...` | ✅ Validado |
| `+0x11BE`–`0x11FE` | **Protagonista** | `We didn't do too well, today...`<br>`(Sigh...) Let's go see Master Bron.` | `Não demos muita sorte hoje...`<br>`(Suspiro...) Ver o Mestre Bron.` | ✅ Validado |
| `+0x13DE`–`0x141A` | **Rasho** | `Damn it! We wasted our time!`<br>`I'm ready to go on a rampage!` | `Maldição! Perdemos nosso tempo!`<br>`Estou pronto pra quebrar tudo!` | ✅ Validado |
| `+0x14A8` | **Protagonista** | `Uhh, calm down...okay?` | `Ér, calma aí... tá bom?` | ✅ Validado |
| `+0x152A`–`0x1612` | **Sugar** | `I'm really disappointed...`<br>`It's their fault too! The items shop`<br>`could've kept some in stock for`<br>`Master {PLAYER}.` | `Estou tão desapontada…`<br>`Culpa deles! A loja de itens bem`<br>`que podia ter guardado estoque`<br>`para o Mestre {PLAYER}.` | ✅ Validado |
| `+0x1678` | **Protagonista** | `They can't do that...` | `Eles não podem fazer isso...` | ✅ Validado |
| `+0x16F8`–`0x17CC` | **Kutty & Protagonista** | `Kuu...`<br>`{PARTNER}, are you disappointed`<br>`because there wasn't any food at`<br>`the shop we went to?` | `Kuu...`<br>`{PARTNER}, você ficou chateado`<br>`porque não tinha comida na`<br>`loja em que nós fomos?` | ✅ Validado |
| `+0x18D6`–`0x1958` | **Protagonista** | `Am I scared of the Labyrinth?`<br>`O-Of course not! We're just need`<br>`to find a few materials...` | `Se eu estou com medo do Labirinto?`<br>`C-Claro que não! Nós só precisamos`<br>`encontrar alguns materiais...` | ✅ Validado |
| `+0x1A44`–`0x1B66` | **Protagonista** | `Your sensors can find where`<br>`they are?`<br>`That's great, {PARTNER}!`<br>`By the way... what's a sensor?` | `Seus sensores conseguem achar`<br>`onde eles estão?`<br>`Isso é ótimo, {PARTNER}!`<br>`Aliás... o que é um sensor?` | ✅ Validado |
| `+0x1BF8`–`0x1C2A` | **Rasho** | `Finally! The Labyrinth!`<br>`Time to go on a rampage!` | `Finalmente! O Labirinto!`<br>`Hora de tocar o terror!` | ✅ Validado |
| `+0x1CAE`–`0x1D2E` | **Protagonista** | `We're just looking for weapon`<br>`materials. You don't have to go`<br>`crazy!` | `Só estamos procurando materiais`<br>`de forja. Não precisa perder`<br>`a cabeça!` | ✅ Validado |
| `+0x1D92`–`0x1E5E` | **Sugar** | `It's dangerous in the Labyrinth, but`<br>`we'll be alright!`<br>`{PARTNER} is here to protect you,`<br>`Master {PLAYER}!` | `O Labirinto é perigoso, mas`<br>`nós vamos ficar bem!`<br>`{PARTNER} está aqui para proteger`<br>`você, Mestre {PLAYER}!` | ✅ Validado |
| `+0x1EC4`–`0x1F0E` | **Protagonista** | `Thanks...`<br>`But, {PARTNER}, aren't you scared`<br>`of all the Stray Summons?` | `Valeu...`<br>`Mas, {PARTNER}, você não tem medo`<br>`de todas as Criaturas Errantes?` | ✅ Validado |
| `+0x1F94`–`0x2138` | **Sugar** | `No problem, Master!`<br>`Let's go find weapon materials!`<br>`Uhh, I mean...`<br>`I'm scared!`<br>`I'm really scared,`<br>`Master {PLAYER}!`<br>`Please protect {PARTNER}!`<br>`And {PARTNER} will protect`<br>`Master {PLAYER} in return!` | `Sem problemas, Mestre!`<br>`Vamos buscar os materiais de armas!`<br>`Quer dizer...`<br>`Estou com medo!`<br>`Estou com muito medo,`<br>`Mestre {PLAYER}!`<br>`Por favor, proteja {PARTNER}!`<br>`E {PARTNER} vai proteger o`<br>`Mestre {PLAYER} em troca!` | ✅ Validado |

### 1.4. Retorno à Oficina e Véspera do 1º Combate
| Offset (PSI3) | Personagem | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x2500`–`0x2578` | **Protagonista** | `Now that we gathered enough`<br>`materials, maybe we should go`<br>`back to our workshop?` | `Agora que já juntamos materiais`<br>`suficientes, que tal voltarmos`<br>`para a nossa oficina?` | ✅ Validado |
| `+0x277C`–`0x27F2` | **Protagonista** | `What? Creating something is`<br>`better than breaking them...?`<br>`Ah, I can understand that.` | `O quê? Criar alguma coisa é`<br>`melhor do que quebrar...?`<br>`Ah, isso eu consigo entender.` | ✅ Validado |
| `+0x287E`–`0x29DE` | **Rasho** | `Hey, hey. Is that it? `<br>`Where's all the fighting and`<br>`excitement? I'm not satisfied yet!`<br>`You're the master, right? Why don't`<br>`you just listen to what I say`<br>`and hang out here some more!` | `Ei, ei. Só isso?`<br>`Cadê toda a pancadaria e a`<br>`emoção? Ainda não estou satisfeito!`<br>`Você é o mestre, não é? Por que`<br>`não escuta o que eu digo e`<br>`fica mais um pouco por aqui!` | ✅ Validado |
| `+0x2A6A`–`0x2AB4` | **Protagonista** | `That's your definition of a master?`<br>`Shouldn't it be other way around...?` | `Essa é a sua definição de mestre?`<br>`Não deveria ser o contrário...?` | ✅ Validado |
| `+0x2B52`–`0x2BF8` | **Sugar & Protagonista** | `Okay, let's head back to our`<br>`love nest...`<br>*(Protagonista:)* `Love nest?` | `Certo, vamos voltar para o nosso`<br>`ninho de amor...`<br>`*(Protagonista:)* Ninho de amor?` | ✅ Validado |
| `+0x2D64`–`0x2DA4` | **Protagonista** | `Now that we know our opponent,`<br>`let's get ready for our match!` | `Sabendo quem é o oponente,`<br>`vamos nos preparar para a luta!` | ✅ Validado |
| `+0x2F50`–`0x3068` | **Sanary & Protagonista** | `The first battle will be easy for `<br>`you. I'm saying this because you're`<br>`my master for the moment.`<br>*(Protagonista:)* `For the moment...` | `A primeira luta vai ser moleza!`<br>`Falo isso pois você é o`<br>`meu mestre por enquanto.`<br>`*(Protagonista:)* Por enquanto…` | ✅ Validado |
| `+0x3142`–`0x3248` | **Sugar & Protagonista** | `Let me give you a good luck kiss`<br>`so that we can win this battle...`<br>*(Protagonista:)* `I... uh... That's okay.`<br>`I appreciate the thought, though!` | `Deixa eu te dar um beijo de sorte`<br>`para vencermos a batalha…`<br>`*(Protagonista:)* Eu… ér… Não precisa.`<br>`Mas agradeço a intenção!` | ✅ Validado |

---

## 2. Script `#0302` (`0x085D4DCC`) — Amariss (Mãe): Incentivo para o Torneio

| Offset (PSI3) | Personagem | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x020E`–`0x029A` | **Amariss** | `Your real training is about to`<br>`begin. Win the tournament and become`<br>`a Craftlord like your father.` | `Seu verdadeiro treino vai`<br>`começar. Vença o torneio e seja`<br>`um Lorde como seu pai!` | ✅ Validado |
| `+0x02DE`–`0x034C` | **Amariss** | `The training will be hard, `<br>`but I have faith in you.`<br>`So don't give up.` | `O treinamento será árduo,`<br>`mas eu tenho fé em você.`<br>`Portanto, não desista.` | ✅ Validado |

---

## 3. Script `#0304` (`0x085D51BC`) — Guia de Wystern, Lore dos Lordes Artesãos e Tutorial de *Minérios Místicos*

| Offset (PSI3) | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `+0x0958`–`0x0A88` | **Morador Guia** | `Hi, {PLAYER}. The Central Tower`<br>`is that big building straight up`<br>`the road here.`<br>`If you're looking for the Item Shop,`<br>`it's the first structure across the`<br>`bridge on your left.` | `Oi, {PLAYER}. A Torre Central`<br>`é aquele prédio enorme seguindo`<br>`direto por esta rua.`<br>`Se procura a Loja de Itens,`<br>`é a primeira construção depois da`<br>`ponte à sua esquerda.` | ✅ Validado |
| `+0x0AC8`–`0x0D18` | **Artesão Veterano** | `Do you know why we need Guardian`<br>`Beasts? It's because they're`<br>`invaluable partners for crafting`<br>`and fighting. You can make `<br>`stronger weapons with their help.`<br>`In battle, you can have them`<br>`protect you with their spells.`<br>`That's not everything about them, `<br>`but they hold a special meaning`<br>`to all Craftknights.` | `Sabe por que precisamos de Feras`<br>`Guardiãs? É porque elas são`<br>`parceiras valiosas na forja e na`<br>`batalha. Você cria armas mais`<br>`fortes com a ajuda delas e usa as`<br>`suas magias para se defender.`<br>`E além disso, têm um significado`<br>`especial para todo bom forjador.` | ✅ Validado |
| `+0x0D58`–`0x0ECC` | **Marinheiro** | `Water Scooters are handy vehicles.`<br>`They move swiftly over the water.`<br>`If you want to ride on one, just`<br>`walk down the stairs near`<br>`the waterway.`<br>`Careful now. You can't climb out of`<br>`the water if there are no stairs.` | `Motos d'água são muito práticas.`<br>`Elas deslizam rápido sobre a água.`<br>`Se quiser pilotar uma, basta`<br>`descer as escadas perto`<br>`do canal de água.`<br>`Mas cuidado: você não pode sair`<br>`da água onde não houver escadas.` | ✅ Validado |
| `+0x0F26`–`0x0FD4` | **Garoto Corredor** | `Hey, do you like running?`<br>`You can move faster by running.`<br>`Use the B Button to run;`<br>`I read that in a book somewhere!` | `Ei, você gosta de correr?`<br>`Você se move mais rápido correndo.`<br>`Use o Botão B para correr;`<br>`eu li isso em algum livro por aí!` | ✅ Validado |
| `+0x1372`–`0x1458` | **Fã de Sakuro** | `Master Sakuro, the Craftlord of`<br>`Sapphire is so cool!`<br>`I want to be just like him.`<br>`That makes me his first fan!`<br>`And you can be his second!` | `O Mestre Sakuro, o Lorde da`<br>`Safira, é tão maneiro!`<br>`Quero ser igualzinho a ele.`<br>`Sou o fã número um dele!`<br>`E você pode ser o número dois!` | ✅ Validado |
| `+0x14A4`–`0x1598` | **Fã de Kouren** | `Do you know Master Kouren?`<br>`She's the Craftlord of Ruby!`<br>`She's beautiful and cool...`<br>`I like her so much that she could`<br>`ask me anything she wants!` | `Você conhece a Mestra Kouren?`<br>`Ela é a Lorde do Rubi!`<br>`Ela é linda e incrível...`<br>`Gosto tanto dela que ela poderia`<br>`me pedir qualquer coisa!` | ✅ Validado |
| `+0x15E4`–`0x1776` | **Admirador de Shintetsu** | `Everyone gets so starstruck when`<br>`they talk about Sakuro or Kouren,`<br>`but the only real Craftlord is`<br>`the late Master Shintetsu.`<br>`He had the style and the looks...`<br>`I'll be rooting for you cuz I know`<br>`you'll become just like Shintetsu!` | `Todo mundo fica deslumbrado quando`<br>`fala de Sakuro ou Kouren,`<br>`mas o único Lorde de verdade é`<br>`o falecido Mestre Shintetsu.`<br>`Ele tinha presença e estilo...`<br>`Vou torcer por você, porque sei que`<br>`vai se tornar igual a Shintetsu!` | ✅ Validado |
| `+0x17D2`–`0x198C` | **Engenheiro de Wystern** | `You know something? Every year, `<br>`Wystern sinks just a tiny bit`<br>`into the sea.`<br>`The reason why this city is always`<br>`under construction above the third`<br>`floor is so that we'll be ready`<br>`to migrate to higher ground when`<br>`the lower floors sink.` | `Sabia de uma coisa? Todo ano,`<br>`Wystern afunda um pouquinho`<br>`no mar.`<br>`As obras nos andares de cima`<br>`servem para estarmos prontos`<br>`para migrar quando os pisos`<br>`de baixo afundarem.` | ✅ Validado |
| `+0x1B4C`–`0x1D62` | **Estudioso de Invocações** | `Do you know about Summon Creatures?`<br>`They are creatures that summoners`<br>`call into this world from another.`<br>`But if it is abandoned by the`<br>`summoner for some reason, `<br>`it becomes a Stray Summon.`<br>`It's also called "Stray"`<br>`for short. How do I know these `<br>`details?`<br>`That's a secret.` | `Conhece as Criaturas Invocadas?`<br>`São criaturas que os invocadores`<br>`chamam de outro mundo para este.`<br>`Mas, se ela for abandonada pelo`<br>`invocador por algum motivo,`<br>`torna-se uma Criatura Errante.`<br>`Também a chamam apenas de "Stray".`<br>`Como eu sei de todos esses`<br>`detalhes?`<br>`Isso é segredo.` | ✅ Validado |
| `+0x1D9A`–`0x262C` | **Mestre dos Minérios (Tutorial de Mystic Ore)** | `You there. Would you like to know`<br>`about Mystic Ores?`<br>`Mystic Ore has a special power`<br>`within it.`<br>`You can transform any weapon into a`<br>`special kind with a Mystic Ore.`<br>`It's stronger than a normal weapon`<br>`and comes with an offensive`<br>`elemental attribute.`<br>`...`<br>`Here, I'll give you three Mystic`<br>`Ores that I found years ago.`<br>`...`<br>`And when you restore a weapon made`<br>`with a Mystic Ore into materials,`<br>`the Mystic Ore will return to you.`<br>`But once you break the weapon,`<br>`you will not get it back. `<br>`So use it with caution.` | `Você aí. Gostaria de saber`<br>`sobre os Minérios Místicos?`<br>`O Minério Místico guarda um poder`<br>`especial dentro de si.`<br>`Pode transformar sua arma com`<br>`um Minério Místico na forja.`<br>`Ela fica melhor que o normal`<br>`e ganha até poderes especiais!`<br>`...`<br>`Tome três Minérios Místicos que`<br>`encontrei anos atrás.`<br>`...`<br>`Ao desmontar uma arma feita`<br>`com Minério Místico, ele volta.`<br>`Mas, se quebrar em combate,`<br>`você o perde para sempre!`<br>`Portanto, use-o com cautela.` | ✅ Validado |

---

## 4. Scripts `#0305` e `#0307` (`0x085D601C` / `0x085D668C`) — Wystern Central, Guilda Dourada e Docas

| Script / Offset | Personagem / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `#0305 +0x054C`–`0x05C2` | **Guarda da Obra** | `You're in Middle Wystern.`<br>`It's still under construction,`<br>`so please use caution.` | `Você está em Middle Wystern.`<br>`Ainda está em construção,`<br>`então, por favor, tenha cuidado.` | ✅ Validado |
| `#0305 +0x0606`–`0x0702` | **Membro da Guilda Dourada** | `Hey, you're a Craftknight from`<br>`the Silver Guild, aren't you?`<br>`This here's the Gold Guild.`<br>`If you have nothing to do here,`<br>`move on. You're in our way.` | `Ei, você é um Cavaleiro da`<br>`Guilda Prateada, não é?`<br>`Aqui é a Guilda Dourada.`<br>`Se não tem nada pra fazer aqui,`<br>`circulando. Você está atrapalhando.` | ✅ Validado |
| `#0305 +0x07B0`–`0x08E0` | **Morador do 2º Nível** | `Craftknights of the Silver Guild`<br>`had better not wander around `<br>`the middle floor.`<br>`Many members of the Gold Guild`<br>`don't get along with Craftknights`<br>`of the Silver Guild.` | `Cavaleiros da Guilda Prateada não`<br>`deveriam rondar o andar central.`<br>`Muitos membros da Guilda Dourada`<br>`não se dão bem com eles.` | ✅ Validado |
| `#0307 +0x032A`–`0x0460` | **Viajante do Gato** | `Because of my job, I have to`<br>`move out of Wystern.`<br>`I feel a great loss knowing that I `<br>`can't bring my cat with me.`<br>`I wonder if some kind person will`<br>`be willing to take care of it...` | `Por causa do meu trabalho, terei`<br>`que me mudar de Wystern.`<br>`Sinto um aperto no coração sabendo`<br>`que não posso levar meu gato.`<br>`Será que alguma alma bondosa`<br>`estaria disposta a cuidar dele...?` | ✅ Validado |
| `#0307 +0x04A8`–`0x0540` | **Vigia do Porto** | `Keep away from the ship docked here.`<br>`You wouldn't like it when the owner`<br>`finds you on it...` | `Fique longe do navio atracado aqui.`<br>`Você não vai gostar nada se o dono`<br>`encontrar você a bordo...` | ✅ Validado |