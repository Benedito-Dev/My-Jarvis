# 0011 · Desbloqueio pelo app: o app captura, o backend decide

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

No Passo 4 da Fase 2, o desbloqueio facial precisava levar à tela inicial do app.
O primeiro plano era o backend abrir a janela do OpenCV num processo separado.
No macOS, janelas só podem ser abertas pela thread principal, e no servidor ela
já está ocupada. O Benedito propôs o padrão de mercado: **a tela captura, o servidor decide**.

## Decisão

- O **app** liga a câmera (`getUserMedia`, com `NSCameraUsageDescription` no
  `Info.plist` do Tauri), tira fotos de 640 px em JPEG e envia uma por vez para
  `POST /desbloqueio/quadro`.
- O **backend** detecta, reconhece e confirma (YuNet + SFace + 5 quadros seguidos)
  e responde `{ estado, progresso, usuario, rostos }`. A sessão (`GET /sessao`)
  guarda quem desbloqueou.
- O app **não reconhece nada**: só mostra o vídeo, o quadrado, a mensagem e a barra.
- A lógica "olhar um quadro e decidir" fica em `desbloqueio_facial/desbloqueio.py`,
  compartilhada pela API e pelo comando de terminal (`jarvis` com janela do OpenCV).

## Alternativas consideradas

- **Backend abre a janela do OpenCV num subprocesso:** duas janelas, remendo para
  a limitação do macOS. Descartada antes do commit.
- **App reconhece o rosto e manda "é o Benedito":** a decisão de segurança ficaria
  no lado que pode ser adulterado, e os modelos teriam que ser reescritos em JavaScript.
- **WebSocket com vídeo contínuo:** mais complexo. Uma foto por requisição
  (~16 KB, ~15 ms no backend) já dá uma experiência fluida.

## Consequências

- ✅ Uma janela só, com a tela de bloqueio dentro do app
- ✅ Decisão protegida no backend, com os modelos num lugar só
- ✅ A voz continua no backend (fala conforme o estado)
- ⚠️ A sessão vive na memória do servidor: reiniciou o backend, volta a ficar bloqueado
