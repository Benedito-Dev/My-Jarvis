# 0007 · SFace (OpenCV) para reconhecer rostos

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

O Passo 3 (cadastrar) e o Passo 4 (reconhecer) precisam transformar um rosto
numa **assinatura**, uma lista de números que identifica a pessoa, para comparar
depois. A [0006](0006-yunet-para-detectar-rostos.md) deixou essa escolha em aberto.

Teste no Mac (Apple Silicon), mesma pessoa em quadros diferentes:

| Medida | Resultado |
|---|---|
| Tempo para gerar uma assinatura | ~20 ms |
| Similaridade (cosseno) consigo mesmo | 0,92 a 0,96 (o limite sugerido para "mesma pessoa" é 0,363) |

## Decisão

Usar o **SFace** (`cv2.FaceRecognizerSF`), que já vem no OpenCV, com o modelo
`face_recognition_sface_2021dec.onnx` (licença Apache 2.0, do OpenCV Zoo).

- O modelo tem **37 MB** e por isso **não vai para o git**. É baixado
  automaticamente no primeiro uso (`nucleo/arquivos.py`) e conferido por SHA-256.
- O SFace usa os 5 pontos do rosto (olhos, nariz, boca) que o YuNet já devolve
  para alinhar o rosto antes de gerar a assinatura.

## Alternativas consideradas

- **`face_recognition` (dlib):** abandonada desde 2020, compilação de ~12 min e
  quebra com `setuptools` ≥ 81.
- **Modelo no git:** 37 MB incham o repositório para sempre (cada versão fica no histórico).
- **Git LFS:** resolve o tamanho, mas é mais uma ferramenta para instalar e configurar.

## Consequências

- ✅ Detecção e reconhecimento na mesma biblioteca (OpenCV), sem compilar nada
- ✅ Repositório leve
- ⚠️ O primeiro uso precisa de internet para baixar o modelo
