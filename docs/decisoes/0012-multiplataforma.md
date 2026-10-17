# 0012 · Rodar nos três sistemas (macOS, Linux e Windows)

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

O projeto nasceu no Mac e a [0001](0001-desktop-nao-web.md) declarava
Windows/Linux fora de escopo. Mas o Benedito usa **três máquinas pessoais**:
Linux, Windows e Mac. O Jarvis precisa rodar nas três.

Varrendo o repositório, a organização por habilidade
([0004](0004-organizacao-por-habilidade.md)) já tinha isolado quase tudo. Só
havia **um** bloqueio funcional de verdade:

| Parte | Situação |
|---|---|
| `nucleo/voz.py` | ❌ o comando `say` existe só no macOS |
| OpenCV (câmera, YuNet, SFace) | ✅ igual nos três |
| `nucleo/caminhos.py` | ✅ caminho relativo ao repositório |
| Tauri | ✅ os três são alvos oficiais dele |
| Frontend React | ✅ só usa `getUserMedia` e `fetch`, nada do Tauri |

## Decisão

**Suportar os três sistemas**, com a diferença concentrada em um lugar só.

A fala passa a ter um **motor de voz por sistema**, em `nucleo/motor_voz.py`,
escolhido por `sys.platform`. Ele só monta o comando; as regras de *quando*
falar continuam no `Locutor` ([0008](0008-say-do-macos-para-falar.md)).

```
nucleo/voz.py        Locutor: quando falar (não repetir, não atropelar)
      │ usa
      ▼
nucleo/motor_voz.py  qual comando falar, por sistema
   darwin → say -v Luciana "<frase>"
   linux  → spd-say -w -l pt "<frase>"      (cancelar: spd-say -C)
   win32  → ainda não: fica mudo
```

Duas diferenças do Linux moldaram a interface do motor:

- **`-w` é obrigatório.** Sem ele o `spd-say` entrega a frase ao daemon e sai em
  ~9 ms (medido), enquanto com `-w` ele dura a fala inteira (6,8 s numa frase
  longa). O `Locutor` usa `Popen.poll()` para saber se ainda está falando, então
  sem `-w` ele acharia que toda fala terminou na hora.
- **Cancelar é um comando separado.** Matar o `spd-say` não cala o daemon, que
  continua falando. Por isso o motor expõe um `cancelar` opcional, usado no
  `interromper=True` das boas-vindas. No macOS matar o processo basta.

Em sistema sem motor, o Locutor **fica mudo e o Jarvis continua funcionando**:
ficar sem voz nunca pode impedir o desbloqueio.

## Alternativas consideradas

- **Piper TTS (voz neural local) nos três:** daria a *mesma* voz, bem mais
  natural, em todos os sistemas. Mas baixa ~60 MB de modelo e ainda precisaria
  de uma saída de áudio por sistema (`afplay`/`aplay`/`winsound`). Passo grande
  demais agora; o `MotorDeVoz` é exatamente o encaixe para trocar depois.
- **`pyttsx3`:** mais uma dependência e, no macOS, usa o mesmo motor do `say`
  por baixo (já recusada na [0008](0008-say-do-macos-para-falar.md)).
- **Manter só o macOS e usar o navegador nas outras máquinas:** o Tauri roda
  nativo nos três; abrir mão da janela nativa não se justificava.

## Consequências

- ✅ O mesmo código roda nos três sistemas, com a diferença em um arquivo só
- ✅ A suíte de testes passa em qualquer máquina: `motor_voz` é função pura
  (texto → lista de argumentos) e o `Locutor` recebe o motor injetado. Antes,
  `test_voz.py` exigia o comando `say` e só passava no Mac
- ✅ O CI (`.github/workflows/testes.yml`) roda a suíte nos três sistemas a cada
  push, então "funciona nos três" é verificado, não prometido. Gratuito por ser
  repositório público — em repositório privado, minuto de macOS conta 10×
- ⚠️ **A voz soa diferente em cada sistema.** No Linux o espeak-ng é bem
  robótico e só tem pt-PT, não pt-BR. Resolver isso é o passo do Piper
- ⚠️ **Os rostos cadastrados não viajam entre as máquinas.** `backend/dados/`
  está no `.gitignore` (dado pessoal não vai para o git), então cada máquina
  precisa do seu próprio cadastro. Como isso se repete em três máquinas, o
  cadastro passou a caber no próprio app (botão "Cadastrar rosto"), sem terminal
- ⚠️ **Windows ainda não verificado.** Falta o motor de voz SAPI. A origem
  CORS do Windows (`http://tauri.localhost`, já que lá o webview não usa
  `tauri://`) já está liberada e coberta por teste
- ⚠️ Os números das decisões [0006](0006-yunet-para-detectar-rostos.md) e
  [0007](0007-sface-para-reconhecer-rostos.md) foram medidos no Mac. Valem como
  referência, não como promessa nas outras máquinas
- ⚠️ Cada sistema tem o seu pré-requisito de build do Tauri (ver
  [`02-stack.md`](../02-stack.md)): no Linux, as libs do WebKitGTK
