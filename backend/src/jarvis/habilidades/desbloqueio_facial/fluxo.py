"""Orquestra a habilidade: liga a entrada (câmera) à lógica e à saída (tela)."""

from pathlib import Path

from jarvis.habilidades.desbloqueio_facial import banco_rostos, tela
from jarvis.habilidades.desbloqueio_facial.camera import Camera
from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    DetectorDeRostos,
    ExtratorDeAssinaturas,
)

# Várias amostras (com o rosto levemente virado) deixam o reconhecimento mais robusto.
AMOSTRAS_CADASTRO = 5


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
                if tela.mostrar(quadro) is tela.Acao.SAIR:
                    break
        finally:
            tela.fechar()


def cadastrar(nome: str) -> Path | None:
    """Captura amostras do rosto com ESPAÇO e salva. Retorna None se o usuário cancelar."""
    detector = DetectorDeRostos()
    extrator = ExtratorDeAssinaturas()
    assinaturas = []

    with Camera() as camera:
        try:
            while len(assinaturas) < AMOSTRAS_CADASTRO:
                quadro = camera.ler_quadro()
                if quadro is None:
                    return None
                limpo = quadro.copy()  # a assinatura sai da imagem sem desenhos
                rostos = detector.detectar(quadro)

                tela.desenhar_rostos(quadro, rostos)
                tela.escrever(quadro, _mensagem_cadastro(len(rostos), len(assinaturas)))
                tela.escrever(quadro, "Vire levemente o rosto entre as capturas", linha=1)

                acao = tela.mostrar(quadro)
                if acao is tela.Acao.SAIR:
                    return None
                if acao is tela.Acao.CAPTURAR and len(rostos) == 1:
                    assinaturas.append(extrator.extrair(limpo, rostos[0]))
        finally:
            tela.fechar()

    return banco_rostos.salvar(nome, assinaturas)


def _mensagem_cadastro(quantidade_rostos: int, capturadas: int) -> str:
    if quantidade_rostos == 0:
        return "Nenhum rosto. Aproxime seu rosto da camera"
    if quantidade_rostos > 1:
        return "Apenas uma pessoa por vez"
    return f"ESPACO para capturar ({capturadas}/{AMOSTRAS_CADASTRO})"
