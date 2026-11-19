# 03 — Mensagens do Sistema, Menus, Interface e Combate
**Jogo:** [NOME DO JOGO]  
**Plataforma:** GBA / [CONSOLA]  
**Status do Arquivo:** Em Construção  

Este documento reúne todas as cadeias de texto da interface de usuário (**UI**), telas de opções, avisos de sistema, mensagens de combate em tempo real e pop-ups de confirmação.

---

## 1. Menus Principais, Telas de Opções e Salvamento

| Endereço / Offset | Função / Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Limite / Obs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `0x08...` | Menu Principal | `Start Game` | `Iniciar Jogo` | Max 14 caracteres | ⏳ Pendente |
| `0x08...` | Menu Principal | `Continue` | `Continuar` | Max 14 caracteres | ⏳ Pendente |
| `0x08...` | Menu Principal | `Options` | `Opções` | Max 14 caracteres | ⏳ Pendente |
| `0x08...` | Diálogo de Save | `Save your progress?` | `Deseja salvar o jogo?` | Janela de confirmação | ⏳ Pendente |
| `0x08...` | Diálogo de Save | `Save complete!` | `Jogo salvo com sucesso!` | Aviso de sucesso | ⏳ Pendente |
| `0x08...` | Diálogo de Load | `The save data is corrupt.` | `Os dados salvos estão corrompidos.` | Erro de leitura SRAM | ⏳ Pendente |

---

## 2. Interface de Combate e Mensagens de Batalha

| Endereço / Offset | Evento de Combate | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Limite / Obs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `0x08...` | Ação de Luta | `Attack` | `Atacar` | Botão HUD de ação | ⏳ Pendente |
| `0x08...` | Ação de Magia | `Magic / Skill` | `Magia / Habilidade` | Seleção de poder | ⏳ Pendente |
| `0x08...` | Ação de Fuga | `Escape` | `Fugir` | Ação de retirada | ⏳ Pendente |
| `0x08...` | Log de Combate | `{PLAYER} dealt {NUMBER} damage!` | `{PLAYER} causou {NUMBER} de dano!` | Log dinâmico | ⏳ Pendente |
| `0x08...` | Fim de Combate | `Victory!` | `Vitória!` | Tela de recompensas | ⏳ Pendente |
| `0x08...` | Fim de Combate | `You were defeated...` | `Você foi derrotado...` | Tela de Game Over | ⏳ Pendente |

---

## 3. Alertas de Sistema e Avisos em Geral

| Endereço / Offset | Contexto | Texto Original (EN-US) | Tradução Sugerida (PT-BR) | Limite / Obs | Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| `0x08...` | Janela de Tutorial | `Press [A] to interact.` | `Aperte [A] para interagir.` | Caixa flutuante | ⏳ Pendente |
| `0x08...` | Inventário Cheio | `Your bag is full!` | `Sua bolsa está cheia!` | Alerta no baú | ⏳ Pendente |
| `0x08...` | Porta Trancada | `The door is firmly locked.` | `A porta está trancada com firmeza.` | Interação em mapa | ⏳ Pendente |
