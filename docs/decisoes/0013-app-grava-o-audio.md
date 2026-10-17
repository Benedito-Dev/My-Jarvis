# 0013 · O app grava o áudio, não o Python

- **Status:** ✅ Aceita
- **Data:** 2026-10-17

## Contexto

Na Fase 3 o Jarvis passa a ouvir. A primeira pergunta é quem captura o som:
o app (API web do navegador) ou o backend em Python.

## Decisão

**O app captura**, com o `MediaRecorder`, e manda o áudio pronto para o backend
guardar. Mesma regra já adotada para o rosto na
[0011](0011-app-captura-backend-decide.md).

O peso disso é multiplataforma ([0012](0012-multiplataforma.md)): `MediaRecorder`
e `getUserMedia` são APIs web, iguais no macOS, no Linux e no Windows. Foi assim
que a câmera funcionou nos três sem uma linha específica de sistema.

Em Python seria o oposto: três backends de áudio diferentes (CoreAudio, PortAudio,
WASAPI), enumeração de dispositivos por sistema e mais uma dependência binária —
recriando no áudio exatamente o problema que o `say` criou na voz.

### O formato muda por sistema

O `MediaRecorder` entrega o que cada webview sabe gravar: webm/ogg no WebKitGTK
(Linux), mp4 no WKWebView (macOS). Por isso o app escolhe o primeiro formato
suportado (`escolherFormato`) e o backend aceita webm, ogg, mp4, mp3 e wav,
recusando o resto com 415.

## Alternativas consideradas

- **Gravar no Python (`sounddevice`/PortAudio):** daria controle fino e serviria
  melhor a uma escuta sempre ligada no futuro, mas traz três backends de áudio
  e uma dependência binária por sistema.
- **Gravar no Python só no Linux:** o pior dos dois mundos — dois caminhos para
  manter, contra a regra da [0012](0012-multiplataforma.md).

## Consequências

- ✅ Áudio multiplataforma sem código específico de sistema
- ✅ Coerente com a [0011](0011-app-captura-backend-decide.md): o app captura,
  o backend decide
- ✅ O microfone liga ao segurar ESPAÇO e desliga ao soltar: o app não escuta
  sozinho
- ⚠️ Precisou liberar `PermissionKind::Microphone` no `src-tauri/src/lib.rs`,
  pelo mesmo motivo da câmera: o WebKitGTK nega calado
- ⚠️ O arquivo gravado tem formato diferente em cada sistema. Quando entrar a
  transcrição, ela vai precisar aceitar todos (o Whisper aceita, via ffmpeg)
- ⚠️ **Escuta sempre ligada** (palavra de ativação, passo 5 da Fase 3) não cabe
  bem neste desenho. Se for por esse caminho, a decisão volta à mesa
- ⚠️ As gravações ficam em `backend/dados/gravacoes/`, fora do git, como todo
  dado pessoal
