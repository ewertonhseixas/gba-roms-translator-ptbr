# Projeto de Tradução: Summon Night - Swordcraft Story

## Etapa 1: Preparação e Ferramentas
- [ ] Baixar e configurar o emulador mGBA ou VisualBoyAdvance-M.
- [ ] Baixar o editor hexadecimal e de gráficos CrystalTile2.
- [ ] Fazer backup da ROM original em inglês.

## Etapa 2: Extração de Texto e Mapeamento
- [ ] Identificar a tabela de caracteres do jogo (TBL).
- [ ] Localizar os ponteiros (pointers) que controlam o início das frases.
- [ ] Desenvolver ou adaptar um script para extrair os diálogos para um formato de texto editável.

## Etapa 3: Edição de Gráficos e Fontes
- [ ] Localizar a fonte do jogo dentro da ROM.
- [ ] Desenhar caracteres acentuados em português (Ç, Ẽ, Á, etc.) substituindo símbolos não utilizados.
- [ ] Atualizar a tabela de texto para reconhecer os novos caracteres.

## Etapa 4: Tradução e Adaptação
- [ ] Traduzir os textos extraídos mantendo as tags de controle do jogo.
- [ ] Adaptar o tamanho do texto ao limite da caixa de diálogo.

## Etapa 5: Inserção e Recálculo de Ponteiros
- [ ] Inserir os textos traduzidos de volta na ROM.
- [ ] Recalcular os ponteiros se o texto traduzido for maior que o original, apontando para o espaço livre.
- [ ] Testar no emulador para garantir que não há erros de exibição ou travamentos.