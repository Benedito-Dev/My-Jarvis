# 0016 · Whisper local (faster-whisper "small") para transcrever a voz

- **Status:** ✅ Aceita
- **Data:** 2026-10-19

## Contexto

Na Fase 3 o Jarvis já grava a voz ([0013](0013-app-grava-o-audio.md)). O passo
seguinte é entender o que foi dito, para depois responder a comandos.

## Decisão

**O backend transcreve com o `faster-whisper`, modelo `small`, rodando na CPU
da máquina.** A rota `POST /conversa/gravacao` guarda o áudio e já devolve o
`texto`; enquanto isso, o núcleo do painel fica no estado "pensando".

- O modelo (~460 MB) é baixado no primeiro uso para
  `habilidades/conversa/modelos/` (fora do git) e carregado ao subir o servidor.
- `JARVIS_WHISPER=base` troca por um modelo 3x menor numa máquina fraca.
- Sem "tentar de novo" (`temperature=0`, `beam_size=1`): com fala repetida, as
  novas tentativas faziam uma frase de 5 s levar 11 s.

Testado com a voz Luciana dizendo "Jarvis, que horas são agora? E qual é a
previsão do tempo para amanhã?": o `small` acertou tudo; o `base` escreveu
"que oraçam agora".

## Alternativas consideradas

- **`base`:** 3x menor e mais rápido, mas errou justamente "que horas são".
- **Transcrição na nuvem (API):** mais rápida, mas a voz sairia da máquina e
  dependeria de internet e de chave de API.
- **Web Speech API no app:** não existe igual nos três WebViews ([0012](0012-multiplataforma.md)).

## Consequências

- ✅ Funciona offline e a voz não sai da máquina
- ✅ Igual nos três sistemas: `faster-whisper` e `av` têm pacote pronto para eles
- ✅ O "pensando" do núcleo passa a ser tempo de verdade
- ⚠️ ~460 MB de download no primeiro uso e ~500 MB de memória com o servidor ligado
- ⚠️ Na CPU de um M1, uma frase curta levou de 3 a 5 s, mas medido com a
  máquina sobrecarregada (carga 28). Falta medir com ela livre
- ⚠️ `av` fixado abaixo de 14: o `faster-whisper` 1.2 usa um parâmetro que saiu do `av` 14
