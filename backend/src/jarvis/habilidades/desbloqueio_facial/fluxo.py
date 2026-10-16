"""Orquestra a habilidade: liga a entrada (câmera) à saída (tela)."""

from jarvis.habilidades.desbloqueio_facial import tela
from jarvis.habilidades.desbloqueio_facial.camera import Camera
from jarvis.habilidades.desbloqueio_facial.reconhecedor import DetectorDeRostos


def executar() -> None:
    """Mostra o vídeo com os rostos marcados até o usuário apertar q/ESC ou fechar a janela."""
    detector = DetectorDeRostos()
    with Camera() as camera:
        try:
            while True:
                quadro = camera.ler_quadro()
                if quadro is None:
                    break
                tela.desenhar_rostos(quadro, detector.detectar(quadro))
                if not tela.mostrar(quadro):
                    break
        finally:
            tela.fechar()
