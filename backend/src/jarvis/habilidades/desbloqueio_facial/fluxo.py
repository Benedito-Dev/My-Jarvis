"""Orquestra a habilidade: liga a entrada (câmera) à saída (tela)."""

from jarvis.habilidades.desbloqueio_facial import tela
from jarvis.habilidades.desbloqueio_facial.camera import Camera


def executar() -> None:
    """Mostra o vídeo da webcam até o usuário apertar q/ESC ou fechar a janela."""
    with Camera() as camera:
        try:
            while True:
                quadro = camera.ler_quadro()
                if quadro is None:
                    break
                if not tela.mostrar(quadro):
                    break
        finally:
            tela.fechar()
