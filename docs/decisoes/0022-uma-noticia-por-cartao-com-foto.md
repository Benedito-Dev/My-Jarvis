# 0022 · Uma notícia por cartão, com foto do Bing e uma da sua região

- **Status:** ✅ Aceita
- **Data:** 2026-10-21

## Contexto

No bom dia ([0021](0021-bom-dia-sem-ia-e-noticias-por-rss.md)), as três
manchetes vinham num cartão só, sem foto, e todas do Brasil. O dono pediu um
cartão por notícia, de preferência com a imagem da manchete, e uma notícia do
Ceará. O feed do Google Notícias não traz foto, e os links dele não levam
direto à matéria (não dá para ler a foto da página).

## Decisão

**Duas manchetes do Brasil + uma da região, cada uma no seu cartão, com a foto
da mesma notícia achada no Bing Notícias.**

- Brasil: as principais do Google Notícias (por importância), como antes.
- Região: busca do Google Notícias nas últimas 24 h por `JARVIS_NOTICIAS_LOCAL`
  (no `.env`: Ceará; sem ela, a cidade do clima). A que repete uma do Brasil é pulada.
- Foto: busca o título no RSS do Bing Notícias, que traz miniatura. Ela só vale
  se metade das palavras importantes do título aparecer no do Bing. Senão o
  cartão fica sem foto, porque uma foto errada é pior que nenhuma. Título longo
  demais (o Bing não acha nada) tenta de novo com as 8 primeiras palavras.
- Só são aceitas fotos servidas pelo próprio Bing (`https://www.bing.com/th?`):
  o app nunca carrega um endereço qualquer vindo de um feed.
- Uma fala por manchete ("Nas notícias:", "E mais:", "Na sua região:"), e o
  cartão de cada uma sobe junto com a sua fala.
- Os três assuntos do bom dia são buscados ao mesmo tempo: ~2 s em vez de ~5 s.

## Alternativas consideradas

- **g1 (o feed já traz foto e resumo):** o feed principal é por horário e cheio
  de notícia policial local. Ficou ruim para um resumo do dia.
- **Abrir o link do Google e ler a foto da matéria:** o link é um
  redirecionamento que só funciona no navegador.
- **Só o Bing:** a busca dele mistura notícias de semanas atrás.

## Consequências

- ✅ Cartões com foto em 10 de 10 manchetes testadas
- ✅ Uma notícia da região no bom dia
- ⚠️ Depende de dois serviços (Google e Bing). Sem o Bing, os cartões ficam sem foto, mas continuam funcionando
- ⚠️ Abrir a foto faz o app pedir a imagem ao Bing (ele vê o IP, não o que foi falado)
