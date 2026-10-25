# ⚔️ Tradução PT-BR: Summon Night - Swordcraft Story 2 (GBA)

> [!NOTE]
> **Aviso Legal:** Esta tradução é um projeto de fãs sem fins lucrativos. A ROM original não é distribuída neste repositório. O usuário deve utilizar sua própria cópia legal da ROM original (`Summon Night - Swordcraft Story 2 (USA).gba`).

---

## 📁 Estrutura do Projeto

```
Summon_Night_Swordcraft_Story_2/
  ├── rom/
  │     ├── Summon Night - Swordcraft Story 2 (USA).gba   # ROM original (16 MB)
  │     └── Summon Night - Swordcraft Story 2 (PT-BR).gba # ROM compilada em PT-BR
  ├── ARQUIVOS md/                                        # 18 Lotes de diálogos extraídos em Markdown
  │     ├── Lote_01_Scripts_0001_a_0178.md
  │     ├── ...
  │     └── Lote_18_Scripts_2407_a_2544.md
  ├── tools/                                              # Ferramentas Python dedicadas ao jogo
  │     ├── archive_extractor.py                          # Extrator dos 5 Master Archives
  │     ├── extract_dialogues_to_md.py                    # Extrator de textos e diálogos PSI3
  │     ├── translation_validator_app.py                  # Interface web de revisão e validação
  │     └── validator_ui.html                             # UI visual em Pixel Art
  ├── docs/
  │     └── architecture.md                               # Mapeamento técnico de memória, VM e ponteiros
  ├── releases/                                           # Patches IPS gerados para distribuição
  ├── Compilar_ROM_PTBR.bat                               # Compilação em 1 clique
  └── Iniciar_Validador_Traducao.bat                      # Inicia validador visual no navegador
```

---

## 🚀 Como Traduzir

1. **Abra os arquivos em `ARQUIVOS md/`**:
   - Cada tabela possui o texto original em inglês na 4ª coluna e o campo vazio `Tradução PT-BR` na 5ª coluna.
   - Preencha com o texto em português.
   - Variáveis dinâmicas como `{PLAYER}`, `{PARTNER}`, `{SIBLING}`, `{MASTER}` devem ser mantidas intactas.
2. **Ou utilize a interface gráfica**:
   - Execute [Iniciar_Validador_Traducao.bat](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/02_TRADUCAO_ROMS_GBA/jogos/Summon_Night_Swordcraft_Story_2/Iniciar_Validador_Traducao.bat) para abrir o visualizador de diálogos com contagem de caracteres por linha e prévia em pixel art.
3. **Compile a qualquer momento**:
   - Execute [Compilar_ROM_PTBR.bat](file:///f:/USER/Documents/Antigravity/Tradução%20GBA/02_TRADUCAO_ROMS_GBA/jogos/Summon_Night_Swordcraft_Story_2/Compilar_ROM_PTBR.bat) para reinserir as frases traduzidas e testar no emulador mGBA.
