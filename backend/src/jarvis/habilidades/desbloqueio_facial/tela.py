"""Saída: mostra o vídeo numa janela do OpenCV. Não decide nada."""

from enum import Enum, auto

import cv2
import numpy as np

from jarvis.habilidades.desbloqueio_facial.reconhecedor import Rosto

NOME_JANELA = "Jarvis"
TECLAS_SAIR = {ord("q"), 27}  # q ou ESC
TECLA_CAPTURAR = ord(" ")  # espaço
VERDE = (0, 255, 0)  # o OpenCV usa BGR
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)


class Acao(Enum):
    """O que o usuário pediu na última tecla."""

    CONTINUAR = auto()
    CAPTURAR = auto()
    SAIR = auto()


def desenhar_rostos(quadro: np.ndarray, rostos: list[Rosto]) -> None:
    """Desenha um quadrado verde em volta de cada rosto (altera o quadro)."""
    for rosto in rostos:
        cv2.rectangle(quadro, (rosto.esquerda, rosto.topo), (rosto.direita, rosto.base), VERDE, 2)


def escrever(quadro: np.ndarray, texto: str, linha: int = 0) -> None:
    """Escreve uma mensagem no canto superior esquerdo (altera o quadro).

    A fonte do OpenCV não tem acentos, então escreva as mensagens sem acento.
    """
    posicao = (20, 40 + linha * 40)
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(quadro, texto, posicao, fonte, 1, PRETO, 5, cv2.LINE_AA)  # contorno
    cv2.putText(quadro, texto, posicao, fonte, 1, BRANCO, 2, cv2.LINE_AA)


def mostrar(quadro: np.ndarray) -> Acao:
    """Mostra o quadro e retorna o que o usuário pediu."""
    cv2.imshow(NOME_JANELA, quadro)
    tecla = cv2.waitKey(1) & 0xFF
    janela_fechada = cv2.getWindowProperty(NOME_JANELA, cv2.WND_PROP_VISIBLE) < 1
    if tecla in TECLAS_SAIR or janela_fechada:
        return Acao.SAIR
    if tecla == TECLA_CAPTURAR:
        return Acao.CAPTURAR
    return Acao.CONTINUAR


def fechar() -> None:
    cv2.destroyAllWindows()
    cv2.waitKey(1)  # no macOS, a janela só some após processar mais um evento
