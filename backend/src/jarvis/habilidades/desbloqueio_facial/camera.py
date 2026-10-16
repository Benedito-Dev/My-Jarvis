"""Entrada: captura quadros da webcam. Não decide nada."""

import cv2
import numpy as np


class CameraIndisponivelError(RuntimeError):
    """A webcam não abriu (sem permissão, em uso por outro app ou inexistente)."""


class Camera:
    """Webcam usada como gerenciador de contexto, para sempre liberar o hardware.

    Exemplo:
        with Camera() as camera:
            quadro = camera.ler_quadro()
    """

    def __init__(self, indice: int = 0) -> None:
        self._indice = indice
        self._captura: cv2.VideoCapture | None = None

    def __enter__(self) -> "Camera":
        self._captura = cv2.VideoCapture(self._indice)
        if not self._captura.isOpened():
            self._captura.release()
            raise CameraIndisponivelError(
                "Não consegui abrir a câmera. Verifique se o app (Terminal/VS Code) "
                "tem permissão em Ajustes > Privacidade e Segurança > Câmera, "
                "e se nenhum outro app está usando a câmera."
            )
        return self

    def __exit__(self, *_: object) -> None:
        if self._captura is not None:
            self._captura.release()
            self._captura = None

    def ler_quadro(self) -> np.ndarray | None:
        """Retorna o quadro atual espelhado (como um espelho), ou None se falhar."""
        if self._captura is None:
            raise RuntimeError("Use a câmera dentro de um bloco `with Camera() as camera:`")
        ok, quadro = self._captura.read()
        if not ok:
            return None
        return cv2.flip(quadro, 1)
