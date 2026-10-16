import numpy as np
import pytest

from jarvis.habilidades.desbloqueio_facial import camera as modulo_camera
from jarvis.habilidades.desbloqueio_facial.camera import Camera, CameraIndisponivelError


class CapturaFalsa:
    """Imita o cv2.VideoCapture para testar sem webcam."""

    def __init__(self, aberta: bool = True, quadro: np.ndarray | None = None) -> None:
        self.aberta = aberta
        self.quadro = quadro
        self.liberada = False

    def isOpened(self) -> bool:  # noqa: N802 (nome da API do OpenCV)
        return self.aberta

    def read(self) -> tuple[bool, np.ndarray | None]:
        return (self.quadro is not None, self.quadro)

    def release(self) -> None:
        self.liberada = True


def usar_captura(monkeypatch: pytest.MonkeyPatch, captura: CapturaFalsa) -> None:
    monkeypatch.setattr(modulo_camera.cv2, "VideoCapture", lambda _indice: captura)


def test_erro_claro_quando_camera_nao_abre(monkeypatch):
    captura = CapturaFalsa(aberta=False)
    usar_captura(monkeypatch, captura)

    with pytest.raises(CameraIndisponivelError, match="permissão"):
        with Camera():
            pass
    assert captura.liberada


def test_quadro_vem_espelhado(monkeypatch):
    quadro = np.array([[[1, 1, 1], [2, 2, 2]]], dtype=np.uint8)  # 1 linha, 2 pixels
    usar_captura(monkeypatch, CapturaFalsa(quadro=quadro))

    with Camera() as camera:
        lido = camera.ler_quadro()

    assert lido is not None
    assert lido[0, 0, 0] == 2 and lido[0, 1, 0] == 1


def test_retorna_none_quando_leitura_falha(monkeypatch):
    usar_captura(monkeypatch, CapturaFalsa(quadro=None))

    with Camera() as camera:
        assert camera.ler_quadro() is None


def test_libera_camera_ao_sair(monkeypatch):
    captura = CapturaFalsa()
    usar_captura(monkeypatch, captura)

    with Camera():
        pass

    assert captura.liberada
