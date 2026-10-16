"""Lógica: encontra rostos numa imagem. Não sabe que existe câmera ou tela."""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# Modelo YuNet do OpenCV Zoo (licença MIT): detector de rostos leve e rápido.
CAMINHO_MODELO = Path(__file__).parent / "modelos" / "face_detection_yunet_2023mar.onnx"

# Detectar na imagem inteira (1280x720) é desperdício. Reduzimos para esta
# largura, detectamos e convertemos as posições de volta para o tamanho original.
LARGURA_DETECCAO = 320

# De 0 a 1: quão confiante o modelo precisa estar para dizer "isto é um rosto".
CONFIANCA_MINIMA = 0.8


@dataclass(frozen=True)
class Rosto:
    """Retângulo de um rosto, em pixels da imagem original."""

    topo: int
    direita: int
    base: int
    esquerda: int


class DetectorDeRostos:
    """Carrega o modelo uma vez e detecta rostos em quantos quadros precisar."""

    def __init__(
        self,
        caminho_modelo: Path = CAMINHO_MODELO,
        largura_deteccao: int = LARGURA_DETECCAO,
        confianca_minima: float = CONFIANCA_MINIMA,
    ) -> None:
        self._largura = largura_deteccao
        # O tamanho de entrada é ajustado a cada quadro em `detectar`.
        self._modelo = cv2.FaceDetectorYN.create(
            str(caminho_modelo), "", (largura_deteccao, largura_deteccao), confianca_minima
        )

    def detectar(self, quadro_bgr: np.ndarray) -> list[Rosto]:
        """Retorna os rostos encontrados no quadro (formato BGR, o padrão do OpenCV)."""
        altura, largura = quadro_bgr.shape[:2]
        escala = self._largura / largura
        tamanho_reduzido = (self._largura, round(altura * escala))
        pequeno = cv2.resize(quadro_bgr, tamanho_reduzido)

        self._modelo.setInputSize(tamanho_reduzido)
        _, deteccoes = self._modelo.detect(pequeno)
        if deteccoes is None:
            return []

        # Cada detecção começa com (x, y, largura, altura) na imagem reduzida.
        return [
            Rosto(
                topo=round(y / escala),
                direita=round((x + w) / escala),
                base=round((y + h) / escala),
                esquerda=round(x / escala),
            )
            for x, y, w, h in deteccoes[:, :4]
        ]
