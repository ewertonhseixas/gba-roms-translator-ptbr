# 🎮 Modelo de Tradução para Novo Jogo GBA

> [!NOTE]
> **Aviso Legal:** Todas as traduções desenvolvidas nesta estrutura são projetos de fãs sem fins lucrativos. **Nenhuma ROM original é distribuída ou disponibilizada no repositório**. Cada usuário deve utilizar sua própria cópia adquirida legalmente do jogo para extrair ou aplicar os patches gerados.

Esta pasta serve como template limpo para você iniciar a tradução de qualquer nova ROM de Game Boy Advance sem afetar os outros jogos ou o projeto de Port.

---

## 📁 Estrutura desta pasta

```
Nome_Do_Jogo/
  ├── rom/                      # Coloque aqui a ROM original (.gba) e onde será gerada a PT-BR
  ├── ARQUIVOS md/              # Textos, tabelas e diálogos extraídos em Markdown para traduzir
  ├── tools/                    # Scripts em Python para extrair/injetar textos, fontes e ponteiros
  ├── releases/                 # Onde ficam os patches (.ips / .ups) prontos para distribuição
  ├── docs/                     # Mapeamento técnico da ROM, memória e notas
  ├── Compilar_ROM_PTBR.bat     # Atalho para compilar a ROM traduzida
  └── Iniciar_Validador.bat     # Atalho para abrir a interface gráfica de validação e edição
```

---

## 🚀 Passo a Passo para Adicionar uma Nova ROM

1. **Duplique esta pasta `_MODELO_NOVO_JOGO`** dentro de `02_TRADUCAO_ROMS_GBA/jogos/` e renomeie para o nome do seu novo jogo (exemplo: `Castlevania_Aria_of_Sorrow` ou `Summon_Night_2`).
2. **Copie a ROM original (.gba)** para dentro da subpasta `rom/`.
3. **Avise no chat o nome da nova ROM**: eu mesmo farei a análise da memória, mapeamento das fontes e extração automática dos textos em arquivos Markdown organizados por lotes.
4. **Traduza ou revise os textos** diretamente nos arquivos `.md` ou usando o aplicativo validador no navegador (`Iniciar_Validador.bat`).
5. **Dê dois cliques em `Compilar_ROM_PTBR.bat`** a qualquer momento para gerar a ROM em português e o patch IPS testável no emulador mGBA (que está na pasta `_ferramentas_gerais/mGBA`).
