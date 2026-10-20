# 0017 · A voz do Jarvis: Piper TTS com a voz "Faber", igual nos três sistemas

- **Status:** ✅ Aceita
- **Data:** 2026-10-19
- **Substitui:** [0008](0008-say-do-macos-para-falar.md)

## Contexto

Cada sistema falava com a voz que tinha: a Luciana do `say` no Mac, o
espeak-ng robótico no Linux e nada no Windows ([0012](0012-multiplataforma.md)).
A Luciana soava como GPS, e o roadmap já previa uma voz só para os três.

O dono também perguntou pelo [VoiceStudio](https://voicestudio.sh/). Ele é
gratuito e local, mas é um app de ~5 GB rodando ao lado do Jarvis, a API dele
documenta só a transcrição e o pt-BR não está confirmado.

## Decisão

**O backend fala com o Piper TTS, voz `pt_BR-faber-medium`, escolhida pelo
dono ouvindo a mesma frase em 8 vozes** (Luciana, 4 do Piper e 3 do Kokoro).

- O Piper gera um .wav por frase, guardado em `dados/voz/` (até 500 arquivos;
  os usados há mais tempo saem).
- O servidor deixa prontas, ao subir, as frases que mais se repetem ("Bem-vindo,
  Benedito", "Por favor, aproxime seu rosto", "Bloqueando. Até logo.").
- Só o **tocador** muda por sistema, em `motor_voz.py`: `afplay` no Mac,
  `paplay`/`aplay`/`pw-play` no Linux e o `SoundPlayer` pelo PowerShell no Windows.
- Se o Piper não puder ser usado, volta para a voz do sistema (`say`, `spd-say`).
- O modelo (~63 MB) é baixado no primeiro uso para `nucleo/modelos/`, com SHA-256 conferido.

## Alternativas consideradas

- **Kokoro:** também bom em pt-BR, mas ~350 MB e 9 a 11 s por frase na CPU.
- **VoiceStudio:** pesado demais para ser uma dependência, e sem uma rota de
  fala documentada.
- **Luciana Premium (macOS):** mais natural, mas só existe no Mac.

## Consequências

- ✅ A mesma voz no Mac, no Linux e no Windows, e o Windows deixa de ser mudo
- ✅ Frases repetidas saem na hora (cache); as novas levam ~1 a 3 s para gerar
- ✅ `JARVIS_MUDO=1` cala o Jarvis (os testes usam isso)
- ✅ Como o áudio é gerado aqui, dá para medir o volume da fala (envelope, a cada
  40 ms). O canal `GET /voz/eventos` avisa o app quando cada fala começa, e o núcleo
  pulsa com a voz de verdade, inclusive em "Bem-vindo" e nos lembretes
- ⚠️ O Piper avisa "Missing phoneme ̃" em sons nasais (são, estão). O dono aprovou a voz assim mesmo
- ⚠️ O tocador do Windows (PowerShell) ainda não foi testado numa máquina Windows
