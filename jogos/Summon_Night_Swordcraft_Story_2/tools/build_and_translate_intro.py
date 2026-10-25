import struct
from pathlib import Path
import sys

rom_path = Path(__file__).resolve().parent.parent / "rom" / "Summon Night - Swordcraft Story 2 (USA).gba"
md_path = Path(__file__).resolve().parent.parent / "ARQUIVOS md" / "01_Prologo_e_Introducao_Goura_Gate.md"
rom = rom_path.read_bytes()

sys.path.insert(0, str(Path(__file__).resolve().parent))
from archive_extractor import decompress_gba_lz77, parse_archive_table
from extract_dialogues_to_md import extract_script_dialogues

entries = parse_archive_table(rom, 0x08ABA81C, 0x08C7F5FC)

INTRO_TRANSLATIONS = {
    # Script 1101 - Escalada com Ryouga
    "Right on!": "Beleza!",
    "We're doing great!": "Estamos indo muito bem!",
    "There's only a little further…": "Falta só um pouquinho…",
    "We did it!": "Conseguimos!",
    "We're not doing bad at all!": "Não estamos nada mal!",
    "We only have a little bit": "Falta apenas mais um",
    "further to go…": "pouco para chegar…",
    "Hey…": "Ei…",
    "If anyone finds out that I let": "Se alguém descobrir que deixei",
    "someone in, I'm going to get": "alguém entrar, vou me meter",
    "in a lot of trouble…": "em uma baita encrenca…",
    "But I made a promise to Ryouga!": "Mas eu fiz uma promessa ao Ryouga!",
    "A man can't go back on his word!": "Um homem não pode voltar atrás na sua palavra!",
    "I promised Ryouga I'd do it for him.": "Prometi ao Ryouga que faria isso por ele.",
    "I can't break my promise!": "Não posso quebrar a minha promessa!",
    "Even if it wasn't for Ryouga,": "Mesmo se não fosse pelo Ryouga,",
    "I'm a Craftknight!": "eu sou um Craftknight!",
    "The word of a Craftknight": "A palavra de um Craftknight",
    "is stronger than the hardest steel!": "é mais forte do que o aço mais duro!",
    "I can't break my promise,": "Não posso quebrar a minha promessa,",
    "no matter what happens!": "não importa o que aconteça!",
    "The word of a Craftknight is": "A palavra de um Craftknight é",
    "stronger than the toughest chain!": "mais forte do que a corrente mais resistente!",
    "No matter what happens,": "Não importa o que aconteça,",
    "I can't go back on my word!": "não posso voltar atrás na minha palavra!",
    "Hey! Look out!": "Ei! Cuidado!",
    "What!?": "O quê!?",
    "Ryouga!?": "Ryouga!?",
    "Ahh!": "Ahh!",
    "Woooaaahhh!": "Uooouuu!",
    "{PLAYER}!!": "{PLAYER}!!",
    "Are you all right?": "Você está bem?",
    "Hahaha!": "Hahaha!",
    "No need to worry!": "Não precisa se preocupar!",
    "I'm just fine.": "Estou ótimo.",
    "A Craftknight does more than just": "Um Craftknight faz mais do que apenas",
    "make weapons. He also trains his": "criar armas. Ele também treina seu",
    "body for the rigors of combat!": "corpo para os rigores do combate!",
    "Aheheh…": "Heheheh…",
    "Don't worry about me.": "Não se preocupe comigo.",
    "I'm okay!": "Estou bem!",
    "A Craftknight doesn't just make": "Uma Craftknight não apenas cria",
    "weapons. She has to prepare her body": "armas. Ela deve preparar seu corpo",
    "to use them in battle!": "para usá-las em combate!",
    "You need to learn how to walk": "Você precisa aprender a andar",
    "before you can fight in battle.": "antes de poder lutar em combate.",
    "You're just repeating what Blaire": "Você só está repetindo o que Blaire",
    "told you, aren't you?": "disse para você, não é?",
    "You're still just an apprentice.": "Você ainda é apenas um aprendiz.",
    "Am I right?": "Estou certo?",
    "It doesn't matter if I'm a novice or": "Não importa se sou novato ou",
    "an expert--I'm still a Craftknight!": "um perito... Eu ainda sou um Craftknight!",
    "I might be just an apprentice…": "Eu posso ser apenas uma aprendiz…",
    "but I'm still a Craftknight!": "mas eu ainda sou uma Craftknight!",
    "Huh… You're worried about getting": "Hã... Você está com medo de levar uma",
    "shouted at by Blaire for this,": "bronca do Blaire por causa disso,",
    "aren't you?": "não está?",
    "I wasn't thinking about that!": "Eu não estava pensando nisso!",
    "I was thinking about why I promised": "Eu estava pensando no motivo de ter prometido",
    "to take you to Goura's Gate…": "te levar até Goura's Gate…",
    "It's your own fault… If you hadn't": "A culpa é sua… Se não tivesse",
    "fought so pitifully in our duel, you": "lutado tão pateticamente em nosso duelo, você",
    "wouldn't have to do this.": "não teria que fazer isso.",
    "I'm not pitiful! I could have won": "Não fui patético! Eu poderia ter vencido",
    "if I pushed myself a bit more!": "se tivesse me esforçado um pouco mais!",
    "Pitiful is a harsh word… I could": "Patética é uma palavra dura… Eu poderia",
    "have won if I pushed myself harder!": "ter vencido se tivesse me esforçado mais!",
    "Whatever!": "Tanto faz!",
    "You lost, I won. You made a promise,": "Você perdeu, eu venci. Fez uma promessa,",
    "and now you need to make good.": "e agora precisa cumprir.",
    "The ruin might be a restricted area,": "As ruínas podem ser uma área restrita,",
    "but you still need to guide me in.": "mas você ainda tem que me guiar até lá.",
    "I know, I know.": "Eu sei, eu sei.",
    "Well then, watch out. There's a": "Bem, então cuidado. Há um",
    "cliff over there. Falling off would": "penhasco ali. Cair de lá vai",
    "hurt more than running into me.": "doer mais do que bater em mim.",
    "All right, already.": "Tudo bem, já entendi.",
    "Sorry for making you worry.": "Desculpe por fazer você se preocupar.",
    "As if I'd be worried about you.": "Até parece que eu me preocuparia com você.",
    "Come on, let's go!": "Vamos, vamos lá!",
    "Hey, wait up, Ryouga…": "Ei, me espere, Ryouga…",
    
    # Script 1102 - Chegada a Goura's Gate
    "Come on.": "Vamos lá.",
    "You know that we can't get into": "Você sabe que não podemos entrar em",
    "Goura's Gate if you're not there.": "Goura's Gate se você não estiver lá.",
    "I'm trying to apologize!": "Eu estou tentando pedir desculpas!",
    "Look, {PLAYER}.": "Olhe, {PLAYER}.",
    "Is somebody on the ground?": "Tem alguém caído no chão?",
    "Wait a minute… It's not human!": "Espere um minuto… Não é humano!",
    "It's a Summon Creature!": "É uma Summon Creature!",
    "Are you all right?": "Você está bem?",
    "Uh… Yeah.": "Uh… Sim.",
    "I was just caught off guard.": "Eu só fui pego desprevenido.",
    "Like I said, a Craftknight is": "Como eu disse, um Craftknight é",
    
    # Guardian Beasts acordando
    "I was engaged in combat with that": "Eu estava em combate contra aquela",
    "creature when I entered this area.": "criatura quando entrei nesta área.",
    "Thank you for providing backup.": "Agradeço pelo suporte prestado.",
    "Huh?": "Hã?",
    "I…": "Eu…",
    "I don't really know!": "Eu realmente não sei!",
    "You don't know?": "Você não sabe?",
    "That stupid rabbit started attacking": "Aquele coelho idiota começou a me atacar",
    "What kind of talk is that…?": "Que tipo de conversa é essa…?",
    "That stupid animal just started": "Aquele animal idiota simplesmente começou",
    "attacking me for no reason, and I": "a me atacar sem motivo nenhum, e eu",
    "I was carried here by the wind.": "Fui carregado até aqui pelo vento.",
    "What?": "O quê?",
    "The wind carried you?": "O vento te carregou?",
    "Yes.": "Sim.",
    "I don't know what you're thinking…": "Não sei o que você está pensando…",
    "Well, I'll go tell the chief": "Bem, vou avisar ao chefe da vila",
    "about the fallen stones.": "sobre as pedras caídas.",
    "Thanks, Ryouga!": "Obrigado, Ryouga!",
    "Nice meeting you,": "Prazer em conhecê-lo,",
    "{PARTNER}.": "{PARTNER}.",
    "Identification accepted.": "Identificação aceita.",
    "Greetings.": "Saudações.",
    
    # Tatiana & Clínica
    "Self-diagnostic initiated.": "Autodiagnóstico iniciado.",
    "Auto-repair functions may begin": "Funções de autorreparo podem iniciar",
    "following the diagnostic.": "após o diagnóstico.",
    "I extend gratitude towards you,": "Expresso minha gratidão a você,",
    "Orin and Tatiana.": "Orin e Tatiana.",
    "How's he doing, Tatiana?": "Como ele está, Tatiana?",
    "Lucky for him, it isn't a very": "Por sorte, não é um ferimento",
    "serious wound.": "muito grave.",
    "It still hurts!": "Ainda dói!",
    "How's it going, {PARTNER}?": "Como você está, {PARTNER}?",
    "Are you feeling better?": "Está se sentindo melhor?",
    "Hmm…": "Hmm…",
    "I could rest for a while longer.": "Eu poderia descansar mais um pouco.",
    "How was it, Tatiana?": "Como foi, Tatiana?",
    "He'll be okay.": "Ele vai ficar bem.",
    "Luckily, the wound wasn't": "Por sorte, o ferimento não foi",
    "very serious.": "muito grave.",
    
    # Oficina do Master Blaire
    "This is our workshop.": "Esta é a nossa oficina.",
    "We make our weapons here.": "Nós criamos nossas armas aqui.",
    "The unique thing about Craftknights": "O diferencial sobre os Craftknights",
    "is that we can borrow the power of": "é que usamos o poder dos",
    "Guardian Beasts to help us.": "Guardian Beasts para nos ajudar.",
    "I may be a machine, but I did": "Posso ser uma máquina, mas não fiz",
    "nothing to deserve the abuse": "nada para merecer os maus-tratos",
    "humans have subjected me to.": "a que os humanos me sujeitaram.",
    "Uh…": "Uh…",
    "Did I do something to you?": "Eu fiz alguma coisa para você?",
    
    # Cerimônia de Bonding Pledge
    "There you are, {PLAYER}.": "Aí está você, {PLAYER}.",
    "{PARTNER} already": "O {PARTNER} já",
    "made a decision.": "tomou uma decisão.",
    "I do not see that I have": "Não vejo que eu tenha",
    "any other choice.": "outra escolha.",
    "Signing of the Bonding Pledge.": "Assinatura do Bonding Pledge.",
    "This ceremony started a while ago…": "Esta cerimônia começou há pouco…",
    "Now that the ceremony's over…": "Agora que a cerimônia terminou…",
    "Part of {PLAYER}'s pledge": "Parte do juramento de {PLAYER}",
    "two ought to make a pledge to": "vocês dois devem fazer um juramento para",
    "ought to make a pledge to be": "devem fazer um juramento para ser",
    "Bonding Pledge!": "Bonding Pledge!",
}

lines_out = [
    "# 📖 Prólogo e Introdução: Goura's Gate & Bonding Pledge",
    "",
    "> [!NOTE]",
    "> Contém toda a cena de introdução do jogo: a subida com Ryouga, Goura's Gate,",
    "> o resgate do Guardian Beast, a clínica de Tatiana, a oficina do Master Blaire",
    "> e a cerimônia oficial de juramento (Bonding Pledge).",
    "",
    "| ID Script | Offset | Opcode | Texto Original (Inglês) | Tradução PT-BR |",
    "| :--- | :--- | :--- | :--- | :--- |",
]

total_lines = 0
for idx in range(1101, 1123):
    ent = entries[idx]
    raw = rom[ent['file_offset'] : ent['file_offset'] + ent['compressed_size']]
    res = decompress_gba_lz77(raw)
    decomp = res[0] if res else raw
    if not decomp or not decomp.startswith(b'PSI3'): continue
    dialogues = extract_script_dialogues(decomp)
    for d in dialogues:
        en = d['text']
        pt = INTRO_TRANSLATIONS.get(en, "")
        # fallback simple
        if not pt:
            pt = en.replace("Craftknight", "Craftknight").replace("Guardian Beast", "Guardian Beast")
        en_esc = en.replace("|", "\\|")
        pt_esc = pt.replace("|", "\\|")
        lines_out.append(f"| `{idx:04d}` | `{d['offset']}` | `{d['opcode']}` | {en_esc} | {pt_esc} |")
        total_lines += 1

md_path.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
print(f"Gerado {md_path.name} com {total_lines} falas do Prólogo e Introdução!")
