# 🎮 Modelo de Tradução para Novo Jogo GBA (Protocolo de Extração v1.0)

> [!NOTE]
> **Aviso Legal:** Todas as traduções desenvolvidas nesta estrutura são projetos de fãs sem fins lucrativos. **Nenhuma ROM original é distribuída ou disponibilizada no repositório**. Cada usuário deve utilizar sua própria cópia adquirida legalmente do jogo para extrair ou aplicar os patches gerados.

Esta pasta serve como template oficial em conformidade com o **[Protocolo Mestre de Extração](../../protocolo_extracao/PROTOCOLO_MESTRE_EXTRACAO.md)** para iniciar a localização de qualquer nova ROM de Game Boy Advance (com suporte expansível para outros consoles) sem afetar os outros jogos ou o projeto de Port.

---

## 📁 Estrutura desta pasta

```
Nome_Do_Jogo/
│
├── rom/                      # Onde inserir a ROM original (.gba) e onde será gerada a PT-BR
│
├── ARQUIVOS md/              # Textos, glossários e tabelas em Markdown estruturados
│   ├── 02-glossario-e-terminologias.md      # Nomes próprios, cidades e termos do universo
│   ├── 03-mensagens-do-sistema.md           # Menus, interface, avisos e combate
│   ├── 06-itens-equipamentos-e-descricoes.md# Arsenal, armas, armaduras e inventário
│   ├── catalogo-de-personagens.md           # Biografia híbrida (in-game + web) e tom de voz
│   ├── estudo-de-metricas-e-caracteres.md   # Estudo de largura e teto de caracteres por linha
│   ├── controle-de-imagens-com-texto.md     # Planilha de controle de tiles/gráficos editados
│   └── Lote_01_Nome_Do_Arco/                # Diálogos divididos por capítulo, fase ou dia
│
├── tools/                    # Scripts Python específicos do jogo (extrator, injetor, fonte)
├── releases/                 # Onde ficam os patches (.ips / .bps) prontos para distribuição
├── docs/                     # Relatório de auditoria, mapa de memória e notas técnicas
│   └── relatorio-extracao.md # Relatório oficial de varredura (vídeos, compressão, dados)
├── Compilar_ROM_PTBR.bat     # Atalho para compilar a ROM traduzida e gerar o patch
└── Iniciar_Validador.bat     # Atalho para abrir a interface gráfica de validação e edição
```

---

## 🚀 Ciclo Operacional para Adicionar uma Nova ROM

1. **Duplique esta pasta `_MODELO_NOVO_JOGO`** dentro de `02_TRADUCAO_ROMS_GBA/jogos/` e renomeie para o nome do novo jogo (ex: `Castlevania_Aria_of_Sorrow`).
2. **Copie a ROM original (.gba)** para dentro da subpasta `rom/`.
3. **Execute o Fingerprint da ROM** utilizando a ferramenta do protocolo:
   ```powershell
   python ../../protocolo_extracao/tools/rom_feature_detector.py rom/seu_jogo.gba -o docs/relatorio-extracao.md
   ```
4. **Extraia os Textos e Dados** em formato Markdown nos arquivos essenciais:
   - `02-glossario-e-terminologias.md`
   - `03-mensagens-do-sistema.md`
   - `06-itens-equipamentos-e-descricoes.md`
   - Lotes de diálogo por capítulos
5. **Execute a Análise de Métricas** para calcular o teto de caracteres por linha e evitar overflow:
   ```powershell
   python ../../protocolo_extracao/tools/metrics_analyzer.py -d "ARQUIVOS md" -g "Nome do Jogo" -l 36
   ```
6. **Preencha o Catálogo de Personagens (`catalogo-de-personagens.md`)** mesclando os dados da ROM com pesquisa em fontes oficiais da web para balizar o tom de voz da tradução.
7. **Traduza com Economia de Tokens** utilizando o particionador de lotes:
   ```powershell
   python ../../protocolo_extracao/tools/token_optimizer_batcher.py "ARQUIVOS md/08-dialogos.md" --chunk-size 35
   ```
8. **Valide no App Web (`Iniciar_Validador.bat`)** e gere a ROM traduzida clicando em `Compilar_ROM_PTBR.bat`.
