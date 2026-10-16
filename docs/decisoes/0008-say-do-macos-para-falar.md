# 0008 · `say` do macOS para o Jarvis falar

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

No Passo 5, o Jarvis passa a falar as mensagens da tela de bloqueio
("Por favor, aproxime seu rosto", "Acesso negado", "Bem-vindo, Roberio").
A fala não pode travar o vídeo.

## Decisão

Usar o comando **`say`**, que já vem no macOS, com a voz **Luciana** (pt-BR),
rodando em paralelo (`subprocess.Popen`). Fica em `nucleo/voz.py` (`Locutor`)
porque falar será útil para todas as habilidades, não só para o desbloqueio.

Regras do `Locutor`, para a fala não virar bagunça:
- enquanto fala, ignora frases novas (exceto com `interromper=True`, usado nas boas-vindas);
- não repete a mesma frase em menos de 6 segundos.

## Alternativas consideradas

- **`pyttsx3`:** mais uma dependência, e no macOS usa o mesmo motor do `say` por baixo.
- **Vozes de IA na nuvem (ex.: ElevenLabs, OpenAI TTS):** voz bem mais natural,
  mas exige internet, chave de API e custo. Pode substituir o `say` no futuro
  sem mudar quem usa o `Locutor`.

## Consequências

- ✅ Zero dependências novas, funciona offline
- ✅ O vídeo continua fluido enquanto o Jarvis fala
- ⚠️ Só funciona no macOS (alinhado com a [0001](0001-desktop-nao-web.md))
- ⚠️ Voz robótica. Dá pra trocar por outra voz instalada (ex.: Felipe) em `VOZ_PADRAO`
