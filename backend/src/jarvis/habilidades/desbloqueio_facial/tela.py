"""Saída: mostra o vídeo numa janela do OpenCV. Não decide nada."""

import cv2
import numpy as np

NOME_JANELA = "Jarvis"
TECLAS_SAIR = {ord("q"), 27}  # q ou ESC


def mostrar(quadro: np.ndarray) -> bool:
    """Mostra o quadro. Retorna False se o usuário pediu para sair."""
    cv2.imshow(NOME_JANELA, quadro)
    tecla = cv2.waitKey(1) & 0xFF
    janela_fechada = cv2.getWindowProperty(NOME_JANELA, cv2.WND_PROP_VISIBLE) < 1
    return tecla not in TECLAS_SAIR and not janela_fechada


def fechar() -> None:
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # no macOS, a janela só some após processar mais um evento
