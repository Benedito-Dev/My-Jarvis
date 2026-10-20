# 0019 · As "mãos" do Jarvis: ferramentas que a IA decide usar

- **Status:** ✅ Aceita
- **Data:** 2026-10-20

## Contexto

Com o cérebro ([0018](0018-cerebro-openrouter-deepseek.md)), o Jarvis conversa,
mas não faz nada no mundo. O próximo degrau é ele **agir**: agendar, pesquisar,
abrir coisas. Ele também não lembrava da conversa: "e amanhã?" não fazia sentido.

## Decisão

**Ferramentas no formato "function calling" do OpenRouter, cada uma uma
`Ferramenta` em `conversa/ferramentas.py`, e memória curta da conversa.**

- A IA recebe a lista de ferramentas e decide sozinha quando usar uma. O
  DeepSeek V4.1 Flash acertou nos testes, até convertendo "às 11 da noite" em minutos.
- Uma ferramenta pode devolver a confirmação já pronta para falar ("Certo. Te
  aviso às 10 e 25."). Aí não há segunda viagem à IA (~2 s a menos).
- No máximo 3 rodadas de ferramentas por pergunta.
- As primeiras ferramentas são `criar_lembrete` e `listar_lembretes`. Na hora, o
  Jarvis fala o lembrete, bloqueado ou não, como um alarme.
- **Memória curta:** as últimas 8 trocas vão junto com cada pergunta. Ela some
  depois de 10 minutos parada ou ao bloquear, para a próxima pessoa não herdar a conversa.
- Pedidos que falam de lembrete, "amanhã", "ontem" etc. saem dos comandos
  fixos e vão para a IA. Antes, "me lembra daqui a 2 horas" respondia a hora atual.
- **Regra para as próximas ferramentas:** o que for irreversível ou falar em
  nome do dono (mandar mensagem, apagar arquivo) pede confirmação antes.

## Alternativas consideradas

- **Reconhecer pedidos com regras fixas** (como hora/data): não escala, porque
  cada jeito de pedir viraria uma regra nova.
- **Framework de agentes (LangChain etc.):** muita dependência para um laço de
  ~30 linhas.

## Consequências

- ✅ Nova habilidade da IA = nova função em `ferramentas.py` e uma linha em `app.py`
- ✅ O painel mostra os lembretes pendentes, com contagem regressiva
- ⚠️ Os lembretes vivem na memória: reiniciar o servidor os perde
- ⚠️ A memória curta também vive só no servidor (nada em disco, por escolha)
