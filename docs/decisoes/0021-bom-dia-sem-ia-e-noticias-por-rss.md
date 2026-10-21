# 0021 · Bom dia montado sem IA, com notícias pelo RSS do Google Notícias

- **Status:** ✅ Aceita
- **Data:** 2026-10-21

## Contexto

O passo 4 da Fase 6: "Jarvis, bom dia" e ele conta o dia (clima, lembretes de
hoje e notícias), falando um assunto de cada vez com um cartão para cada. Havia
duas perguntas: quem monta a fala (a IA ou regras fixas) e de onde vêm as
notícias, já que a busca de notícias do DuckDuckGo é instável.

## Decisão

**O bom dia é um comando fixo, montado sem IA, e as manchetes vêm do RSS do
Google Notícias.**

- `comandos.py` reconhece "bom dia", "resumo do dia" e "briefing" (só isso, mais
  cortesia; "bom dia, vai chover amanhã?" vai para a IA).
- `habilidades/bom_dia/resumo.py` busca os três assuntos e monta as frases a
  partir dos dados. Cada assunto vira uma `Parte`: fala + cartão.
- A API cumprimenta na hora ("Bom dia, Benedito."), busca os assuntos enquanto
  ele fala (a tela mostra o progresso) e depois manda **cada cartão logo antes
  da sua fala**.
- A tela conta as falas que começam a tocar (canal `/voz/eventos`) e só mostra um
  cartão quando a fala dele começa. Assim o cartão do clima sobe com a fala do
  clima, e o das notícias com a das notícias.
- O resumo entra na memória da conversa: "detalha a primeira" funciona pela IA.
- `habilidades/noticias/manchetes.py` lê o feed (grátis, sem chave; dá para
  trocar com `JARVIS_NOTICIAS_RSS`). Também virou ferramenta da IA (`noticias`).
- Só com a sessão aberta. Bloqueado, "bom dia" recebe só "Bom dia.".

## Alternativas consideradas

- **A IA monta o bom dia com as ferramentas:** mais natural, mas mais lento
  (~3 viagens à IA), pode esquecer um assunto e não funciona sem a chave.
- **Notícias pelo DuckDuckGo (`pesquisar_web`):** já existia, mas às vezes volta
  vazio sem motivo. O RSS respondeu sempre nos testes.
- **Feed do g1:** só um jornal. O Google Notícias junta várias fontes e traz o nome de cada uma.

## Consequências

- ✅ Bom dia em ~2 s, de graça e sempre com os três assuntos
- ✅ Cartão e fala andam juntos na tela
- ⚠️ As frases são fixas: menos variadas que as da IA
- ⚠️ O Google Notícias pode mudar o feed; aí basta trocar `JARVIS_NOTICIAS_RSS`
