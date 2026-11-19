# ROMs Translator PT-BR

Ferramentas e protocolos para localizar jogos de **Game Boy Advance** e **Nintendo DS** em português do Brasil. O fluxo cobre extração, organização de textos em Markdown, revisão visual, auditoria e compilação local.

| Pasta | Conteúdo |
| --- | --- |
| [02_TRADUCAO_ROMS_GBA](02_TRADUCAO_ROMS_GBA/) | Protocolos, modelo de projeto, utilitários de QA, editor de imagens e documentação técnica de Summon Night Swordcraft Story. |
| [03_TRADUCAO_ROMS_NDS](03_TRADUCAO_ROMS_NDS/) | Detecção e extração NitroFS, além de pipelines de texto e gráficos para Summon Night e Tales of Hearts. |
| [00_APPS_E_ATALHOS](00_APPS_E_ATALHOS/) | Atalhos Windows para o editor e os validadores dos projetos locais. |

## Validador de textos

O validador abre no navegador e lê as tabelas Markdown da pasta do jogo. A interface inclui prévia de diálogo, controle de quebras de linha, verificação de QA, busca de glossário e fichas de personagens, aprovação em lote e geração de contexto para revisão. O botão de compilação usa o script específico do jogo quando disponível e requer os dados locais esperados por esse script.

Com Python 3 disponível no terminal, execute a partir da raiz:

```powershell
python -X utf8 "02_TRADUCAO_ROMS_GBA/jogos/_MODELO_NOVO_JOGO/tools/translation_validator_app.py"
```

Para um projeto NDS, use o atalho correspondente em `00_APPS_E_ATALHOS`. Os atalhos de Summon Night para GBA buscam as respectivas pastas dos jogos na instalação local. O [editor de imagens](02_TRADUCAO_ROMS_GBA/_ferramentas_gerais/image_editor/) abre com `00_APPS_E_ATALHOS/editor_de_imagens.bat`.

## Extração e vídeo no Nintendo DS

O [guia NDS](03_TRADUCAO_ROMS_NDS/README.md) descreve a estrutura local dos projetos e a auditoria de ROMs. A pasta de ferramentas inclui o detector de recursos e o extrator NitroFS. Os scripts de Tales of Hearts incluem o codec de scripts CRI, aplicação de legendas, comparação de qualidade e checagens para reinserção de vídeos MODS.

O [MobiclipDecoder](https://github.com/Gericom/MobiclipDecoder) é uma dependência externa para decodificar MODS. Os scripts de vídeo usam um FFmpeg convencional em `03_TRADUCAO_ROMS_NDS/_ferramentas_nds/ffmpeg.exe` e uma variante compatível com a codificação MODS em `03_TRADUCAO_ROMS_NDS/_ferramentas_nds/mobipeg/`, com `ffmpeg.exe` e `ffprobe.exe`. Cada etapa depende dos arquivos de vídeo gerados nas etapas anteriores.

## Protocolos

- [Protocolo Mestre de Extração](02_TRADUCAO_ROMS_GBA/protocolo_extracao/PROTOCOLO_MESTRE_EXTRACAO.md)
- [Protocolo Mestre de Tradução](02_TRADUCAO_ROMS_GBA/protocolo_traducao/PROTOCOLO_MESTRE_TRADUCAO.md)
- [Glossário global de Summon Night](02_TRADUCAO_ROMS_GBA/protocolo_traducao/GLOSSARIO_GLOBAL_SUMMON_NIGHT.md)
- [Regras de trabalho](AGENTS.md)

ROMs comerciais, extrações, mídia do jogo, traduções em andamento, builds e executáveis de terceiros são dados locais. Use suas próprias cópias e confira os insumos de cada projeto antes de executar o build.
