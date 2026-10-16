# 0006 · YuNet (OpenCV) para detectar rostos

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

No Passo 2, o vídeo precisa marcar o rosto **em tempo real**. A primeira tentativa,
com `face_recognition`, ficou lenta demais.

Medição no Mac (Apple Silicon), câmera 1280x720, com a pessoa em frente à câmera:

| Detector | Quadros/s | Rosto detectado |
|---|---|---|
| `face_recognition` (HOG, padrão) | 2,3 🐌 | 7/7 |
| `face_recognition` sem upsample | mais rápido, mas **perde rostos mais distantes** | instável |
| **YuNet (`cv2.FaceDetectorYN`)** | **20,5** 🚀 | **82/82** |

## Decisão

Usar o **YuNet**, que já vem no OpenCV, para **detectar** rostos (onde está o rosto).
O modelo (`face_detection_yunet_2023mar.onnx`, 232 KB, licença MIT, do
[OpenCV Zoo](https://github.com/opencv/opencv_zoo)) fica versionado dentro da
habilidade, em `desbloqueio_facial/modelos/`.

`face_recognition` saiu das dependências. **Reconhecer** (de quem é o rosto) será
decidido no Passo 3. Opções: `face_recognition` ou o SFace do próprio OpenCV.

## Alternativas consideradas

- **`face_recognition` (HOG):** lento, e acelerar custa alcance.
- **Detectar a cada N quadros ou numa thread:** esconde a lentidão, mas complica
  o código sem resolver a causa.
- **Haar cascade do OpenCV:** rápido, mas antigo e com muitos falsos positivos.

## Consequências

- ✅ Vídeo fluido (~20 quadros/s) com detecção estável
- ✅ Sem compilação de 12 min do `dlib` por enquanto
- ⚠️ Um arquivo de modelo binário no git (pequeno, 232 KB)
