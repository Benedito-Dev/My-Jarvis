# 0018 · Cérebro de IA: DeepSeek V4.1 Flash pelo OpenRouter

- **Status:** ✅ Aceita (para a fase de testes)
- **Data:** 2026-10-20

## Contexto

Fora dos comandos fixos (hora, data, bloquear), o Jarvis respondia "Ainda não
sei fazer isso". Faltava um cérebro para perguntas livres. O dono já tem conta
no OpenRouter e pediu o modelo DeepSeek mais barato para os testes.

## Decisão

**Perguntas que os comandos não entendem vão para `deepseek/deepseek-v4.1-flash`
pelo OpenRouter.** Ele era o DeepSeek mais barato da lista em 20/10/2026: US$ 0,056
por milhão de tokens de entrada e US$ 0,12 de saída, ~US$ 0,00003 por pergunta.

- Os comandos continuam primeiro, locais e instantâneos: a IA só entra no resto.
- Só com a sessão desbloqueada: com o Jarvis bloqueado, ninguém gasta crédito.
- O "raciocínio" do modelo fica desligado: ~2x mais rápido (1,2 a 2 s), mesma qualidade.
- A personalidade pede respostas curtas e faladas (sem listas nem markdown) e
  números "como se fala". O dia e a hora vão junto na pergunta.
- A chave fica em `backend/.env` (fora do git), lida só quando o servidor sobe.
  Os testes nunca chamam a IA de verdade.
- `JARVIS_MODELO_IA` troca o modelo sem mexer no código.

## Alternativas consideradas

- **Claude (Anthropic):** previsto no roadmap, mas o dono preferiu começar pelo
  OpenRouter, que já tinha. Trocar é mudar `JARVIS_MODELO_IA` (ex.: um modelo
  `anthropic/...` do próprio OpenRouter).
- **Modelo local (Ollama etc.):** sem custo e offline, mas pesado para uma CPU
  que já roda Whisper e Piper.

## Consequências

- ✅ O Jarvis conversa sobre qualquer assunto, com voz e no tom de um Jarvis
- ✅ Custo desprezível nos testes
- ⚠️ Só o TEXTO da pergunta sai da máquina, mas ele sai (para o OpenRouter e o DeepSeek)
- ⚠️ Sem internet ou sem crédito, ele avisa em voz: "Não consegui pensar nisso agora"
- ⚠️ Ainda não lembra do que foi dito antes: cada pergunta é a primeira
