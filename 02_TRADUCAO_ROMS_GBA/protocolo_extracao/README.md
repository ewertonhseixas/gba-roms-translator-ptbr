# 🕹️ Protocolo de Extração para Tradução de ROMs
> **Versão 1.0.0** | Projetado para GBA e extensível para SNES, Mega Drive, NDS e PS1.

Bem-vindo ao **Protocolo Oficial de Extração para Tradução de ROMs**. Este pacote define a metodologia padrão, templates e ferramentas de linha de comando para transformar qualquer ROM de videogame em um ambiente estruturado de tradução, sem desperdício de tokens com IA e com 100% de integração com a nossa suíte de validação interativa.

---

## 📂 Conteúdo deste Diretório

```
protocolo_extracao/
│
├── PROTOCOLO_MESTRE_EXTRACAO.md    # Manual técnico completo e diretrizes arquiteturais
│
├── 📁 templates/                   # Modelos prontos para copiar em novos projetos
│   ├── 02-glossario-e-terminologias.template.md
│   ├── 03-mensagens-do-sistema.template.md
│   ├── 06-itens-equipamentos-e-descricoes.template.md
│   ├── catalogo-de-personagens.template.md
│   ├── estudo-de-metricas-e-caracteres.template.md
│   ├── controle-de-imagens-com-texto.template.md
│   └── relatorio-extracao.template.md
│
└── 📁 tools/                       # Suíte de ferramentas automáticas em Python
    ├── metrics_analyzer.py         # Análise estatística de limites e caracteres por linha
    ├── rom_feature_detector.py     # Varredura de cabeçalho, vídeos (Mobiclip) e compressões
    ├── image_text_auditor.py       # Catalogação e auditoria de imagens com texto
    └── token_optimizer_batcher.py  # Fatia lotes com injeção cirúrgica de contexto (Token Economy)
```

---

## 🛠️ Como Utilizar as Ferramentas

### 1. Auditoria e Fingerprint da ROM (`rom_feature_detector.py`)
Faz a análise inicial do cartucho, identificando serial oficial, compressões da BIOS e presença de FMVs/vídeos que necessitem de legendagem:
```powershell
python protocolo_extracao/tools/rom_feature_detector.py "caminho/para/jogo.gba" -o "docs/relatorio-auditoria-rom.md"
```

### 2. Estudo de Métricas de Caracteres (`metrics_analyzer.py`)
Escaneia os diálogos extraídos, calcula a média e o teto de caracteres por linha e identifica automaticamente se há falas em PT-BR que estouram a largura da janela do jogo:
```powershell
python protocolo_extracao/tools/metrics_analyzer.py -d "ARQUIVOS md" -g "Nome do Jogo" -l 36
```

### 3. Auditoria de Imagens com Texto (`image_text_auditor.py`)
Gera a planilha de controle para todos os gráficos com texto e valida se as imagens editadas respeitam as dimensões em pixels e a paleta original:
```powershell
# Gerar planilha de controle:
python protocolo_extracao/tools/image_text_auditor.py -d "extracted/graphics" -o "ARQUIVOS md/controle-de-imagens-com-texto.md"

# Auditar imagens editadas antes de reinjetar na ROM:
python protocolo_extracao/tools/image_text_auditor.py -d "extracted/graphics" -f "fixes/graphics" --audit
```

### 4. Economia de Tokens para Tradução com IA (`token_optimizer_batcher.py`)
Fatia arquivos longos de diálogo em lotes enxutos de 30-50 falas e injeta **apenas** os termos do glossário e personagens presentes no trecho, economizando até 80% dos tokens:
```powershell
python protocolo_extracao/tools/token_optimizer_batcher.py "ARQUIVOS md/08-dialogos-cap1.md" --glossary "ARQUIVOS md/02-glossario.md" --catalog "ARQUIVOS md/catalogo-de-personagens.md" --chunk-size 35
```
