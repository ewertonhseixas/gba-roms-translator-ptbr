# 07 — Bestiário Completo: Monstros (*Stray Summons*), Inimigos e Chefes

Este documento lista **todos os 106 registros de monstros, variantes elementais, soldados inimigos e chefes** extraídos da tabela de Bestiário da ROM (`0x081F7F68`–`0x081F9D28`), com sugestão de tradução (Opção A — Adaptada para PT-BR) e manutenção de nomes próprios/clássicos de RPG (Opção B).

---

## 1. Criaturas do Labirinto e Masmorras (`0x081F7F68`–`0x081F9268`)

| Endereço ROM | Nome Original (EN-US) | Tradução Sugerida (PT-BR) | Alternativa (Mantendo termos clássicos) | Status |
| :--- | :--- | :--- | :--- | :---: |
| `0x081F7F68` | `Slime` | `Slime` | `Slime` | ✅ Validado |
| `0x081F7FA8` | `Jelly Slime` | `Jelly Slime` | `Jelly Slime` | ✅ Validado |
| `0x081F7FE8` | `Gel Slime` | `Gel Slime` | `Gel Slime` | ✅ Validado |
| `0x081F8028` | `Spirit` | `Spirit` | `Espírito` | ✅ Validado |
| `0x081F8068` | `Evil Spirit` | `Evil Spirit` | `Espírito Maligno` | ✅ Validado |
| `0x081F80A8` | `Gremlin` | `Gremlin` | `Gremlin` | ✅ Validado |
| `0x081F80E8` | `Red Gremlin` | `Red Gremlin` | `Red Gremlin` | ✅ Validado |
| `0x081F8128` | `Spinner` | `Spinner` | `Spinner` | ✅ Validado |
| `0x081F8168` | `Cutter` | `Cutter` | `Cutter` | ✅ Validado |
| `0x081F81A8` | `Pumpkeeno` | `Pumpkeeno` | `Pumpkeeno` | ✅ Validado |
| `0x081F81E8` | `Magikeeno` | `Magikeeno` | `Magikeeno` | ✅ Validado |
| `0x081F8228` | `Halloweeno` | `Halloweeno` | `Halloweeno` | ✅ Validado |
| `0x081F8268` | `Cuckoo` | `Cuckoo` | `Cuckoo` | ✅ Validado |
| `0x081F82A8` | `Glider` | `Glider` | `Glider` | ✅ Validado |
| `0x081F82E8` | `Gunnerhead` | `Gunnerhead` | `Gunnerhead` | ✅ Validado |
| `0x081F8328` | `Sniperhead` | `Sniperhead` | `Sniperhead` | ✅ Validado |
| `0x081F8368` | `Missilehead` | `Missilehead` | `Missilehead` | ✅ Validado |
| `0x081F83A8` | `Garref` | `Garref` | `Garref` | ✅ Validado |
| `0x081F83E8` | `Lycaon` | `Lycaon` | `Lycaon` | ✅ Validado |
| `0x081F8428` | `Wolgan` | `Wolgan` | `Wolgan` | ✅ Validado |
| `0x081F8468` | `Lizardio` | `Lizardio` | `Lizardio` | ✅ Validado |
| `0x081F84A8` | `Harricade` | `Harricade` | `Harricade` | ✅ Validado |
| `0x081F84E8` | `Red Pincher` | `Red Pincher` | `Red Pincher` | ✅ Validado |
| `0x081F8528` | `Black Pincher` | `Black Pincher` | `Black Pincher` | ✅ Validado |
| `0x081F8568` | `Defender` | `Defender` | `Defender` | ✅ Validado |
| `0x081F85A8` | `Interceptor` | `Interceptor` | `Interceptor` | ✅ Validado |
| `0x081F85E8` | `Mud Boxer` | `Mud Boxer` | `Mud Boxer` | ✅ Validado |
| `0x081F8628` | `Mud Sucker` | `Mud Sucker` | `Mud Sucker` | ✅ Validado |
| `0x081F8668` | `Red Dragon` | `Red Dragon` | `Red Dragon` | ✅ Validado |
| `0x081F86A8` | `Dark Dragon` | `Dark Dragon` | `Dark Dragon` | ✅ Validado |
| `0x081F86E8` | `Iron Giant` | `Iron Giant` | `Iron Giant` | ✅ Validado |
| `0x081F8728` | `Gunner Giant` | `Gunner Giant` | `Gunner Giant` | ✅ Validado |
| `0x081F8768` | `Escaroo` | `Escaroo` | `Escaroo` | ✅ Validado |
| `0x081F87A8` | `Snairoo` | `Snairoo` | `Snairoo` | ✅ Validado |
| `0x081F87E8` | `Crystanare` | `Crystanare` | `Crystanare` | ✅ Validado |
| `0x081F8828` | `Aquanare` | `Aquanare` | `Aquanare` | ✅ Validado |
| `0x081F8868` | `Sahagin` | `Sahagin` | `Sahagin` | ✅ Validado |
| `0x081F88A8` | `Mermarion` | `Mermarion` | `Mermarion` | ✅ Validado |
| `0x081F88E8` | `Dragon Puppy` | `Dragon Puppy` | `Dragon Puppy` | ✅ Validado |
| `0x081F8928` | `Flying Lizard` | `Flying Lizard` | `Flying Lizard` | ✅ Validado |
| `0x081F8968` | `Onibi` | `Onibi` | `Onibi` | ✅ Validado |
| `0x081F89A8` | `Hannya` | `Hannya` | `Hannya` | ✅ Validado |
| `0x081F89E8` | `Fire Mage` | `Fire Mage` | `Fire Mage` | ✅ Validado |
| `0x081F8A28` | `Flame Mage` | `Flame Mage` | `Flame Mage` | ✅ Validado |
| `0x081F8A68` | `Brute Monk` | `Brute Monk` | `Brute Monk` | ✅ Validado |
| `0x081F8AA8` | `Giant Monk` | `Giant Monk` | `Giant Monk` | ✅ Validado |
| `0x081F8AE8` | `Pomdog` | `Pomdog` | `Pomdog` | ✅ Validado |
| `0x081F8B28` | `Winderdog` | `Winderdog` | `Winderdog` | ✅ Validado |
| `0x081F8B68` | `Smoggro` | `Smoggro` | `Smoggro` | ✅ Validado |
| `0x081F8BA8` | `Foggro` | `Foggro` | `Foggro` | ✅ Validado |
| `0x081F8BE8` | `Windleon` | `Windleon` | `Windleon` | ✅ Validado |
| `0x081F8C28` | `Chamedeon` | `Chamedeon` | `Chamedeon` | ✅ Validado |
| `0x081F8C68` | `Popper` | `Popper` | `Popper` | ✅ Validado |
| `0x081F8CA8` | `Jumper` | `Jumper` | `Jumper` | ✅ Validado |
| `0x081F8CE8` | `Striker` | `Striker` | `Striker` | ✅ Validado |
| `0x081F8D28` | `Bolt Striker` | `Bolt Striker` | `Bolt Striker` | ✅ Validado |
| `0x081F8D68` | `Squibolt` | `Squibolt` | `Squibolt` | ✅ Validado |
| `0x081F8DA8` | `Sparquid` | `Sparquid` | `Sparquid` | ✅ Validado |
| `0x081F8DE8` | `Tumbler` | `Tumbler` | `Tumbler` | ✅ Validado |
| `0x081F8E28` | `Charger` | `Charger` | `Charger` | ✅ Validado |
| `0x081F8E68` | `Headache` | `Headache` | `Headache` | ✅ Validado |
| `0x081F8EA8` | `Death Head` | `Death Head` | `Death Head` | ✅ Validado |
| `0x081F8EE8` | `Devil Head` | `Devil Head` | `Devil Head` | ✅ Validado |
| `0x081F8F28` | `Dark Demon` | `Dark Demon` | `Dark Demon` | ✅ Validado |
| `0x081F8F68` | `Arch Demon` | `Arch Demon` | `Arch Demon` | ✅ Validado |
| `0x081F8FA8` | `Spell Sword` | `Spell Sword` | `Spell Sword` | ✅ Validado |
| `0x081F8FE8` | `Evil Sword` | `Evil Sword` | `Evil Sword` | ✅ Validado |
| `0x081F9028` | `Spell Axe` | `Spell Axe` | `Spell Axe` | ✅ Validado |
| `0x081F9068` | `Evil Axe` | `Evil Axe` | `Evil Axe` | ✅ Validado |
| `0x081F90A8` | `Spell Lance` | `Spell Lance` | `Spell Lance` | ✅ Validado |
| `0x081F90E8` | `Evil Lance` | `Evil Lance` | `Evil Lance` | ✅ Validado |
| `0x081F9128` | `Killer Sword` | `Killer Sword` | `Killer Sword` | ✅ Validado |
| `0x081F9168` | `Sword Knight` | `Sword Knight` | `Sword Knight` | ✅ Validado |
| `0x081F91A8` | `Killer Axe` | `Killer Axe` | `Killer Axe` | ✅ Validado |
| `0x081F91E8` | `Axe Knight` | `Axe Knight` | `Axe Knight` | ✅ Validado |
| `0x081F9228` | `Killer Lance` | `Killer Lance` | `Killer Lance` | ✅ Validado |
| `0x081F9268` | `Lance Knight` | `Lance Knight` | `Lance Knight` | ✅ Validado |

---

## 2. Chefes (*Bosses*), Criaturas Raras e Oponentes Humanos (`0x081F95E8`–`0x081F9D28`)

| Endereço ROM | Nome Original (EN-US) | Tradução Sugerida (PT-BR) | Contexto no Jogo | Status |
| :--- | :--- | :--- | :--- | :---: |
| `0x081F95E8` | `Yasha Spider` | `Yasha Spider` | Chefe de masmorra. | ✅ Validado |
| `0x081F9628` | `Heavy Metal` | `Heavy Metal` | Chefe mecânico. | ✅ Validado |
| `0x081F9668` | `Giant Serpent` | `Giant Serpent` | Chefe aquático. | ✅ Validado |
| `0x081F96A8` | `Grudge Fish` | `Grudge Fish` | Subchefe / Criatura rara que dropa Minério Místico. | ✅ Validado |
| `0x081F96E8` | `Evil Fish` | `Evil Fish` | Variante de chefe aquático. | ✅ Validado |
| `0x081F9728` | `King Crabber` | `King Crabber` | Chefe aquático. | ✅ Validado |
| `0x081F9768` | `Kirin` | `Kirin` | Fera mítica / Chefe. | ✅ Validado |
| `0x081F97A8`–`98E8` | `Parista` *(6 formas)* | `Parista` | Chefe principal / Entidade selada em Wystern. | ✅ Validado |
| `0x081F9928` | `Evil Metal` | `Evil Metal` | Variante de chefe pós-jogo. | ✅ Validado |
| `0x081F9968` | `Omen Fish` | `Omen Fish` | Variante de chefe pós-jogo. | ✅ Validado |
| `0x081F99A8` | `Inferno Kirin` | `Inferno Kirin` | Variante de chefe pós-jogo. | ✅ Validado |
| `0x081F99E8` / `9CE8` | `Chaves` | `Chaves` | Oponente da 1ª rodada do Torneio. | ✅ Validado |
| `0x081F9A28` / `9D28` | `Varil` | `Varil` | Rival da Guilda Dourada. | ✅ Validado |
| `0x081F9A68` | `Kenon` | `Kenon` | Oponente da 2ª rodada do Torneio. | ✅ Validado |
| `0x081F9AA8` | `Razzy` | `Razzy` | Oponente da 3ª rodada do Torneio. | ✅ Validado |
| `0x081F9AE8` | `Ariel` | `Ariel` | Oponente da 4ª rodada do Torneio. | ✅ Validado |
| `0x081F9B28` / `9BE8` | `Soldier` | `Soldier` | Soldado inimigo em batalha. | ✅ Validado |
| `0x081F9B68`–`9CA8` | `Ureksa` *(3 formas)* | `Ureksa` | Lorde Artesão antagonista em batalha. | ✅ Validado |
| `0x081F9C28` | `Lubert` | `Lubert` | Lorde Artesão Lubert em batalha. | ✅ Validado |
| `0x081F9C68` | `Sanary` | `Sanary` | Oponente da 5ª rodada do Torneio. | ✅ Validado |