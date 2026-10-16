"""Orquestra a habilidade no terminal: liga a webcam à lógica e à janela do OpenCV."""

import time
from pathlib import Path

from jarvis.habilidades.desbloqueio_facial import banco_rostos, tela
from jarvis.habilidades.desbloqueio_facial.camera import Camera
from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    FRASES,
    Desbloqueador,
    EstadoDesbloqueio,
)
from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    DetectorDeRostos,
    ExtratorDeAssinaturas,
)
from jarvis.nucleo.voz import Locutor

# Várias amostras (com o rosto levemente virado) deixam o reconhecimento mais robusto.
AMOSTRAS_CADASTRO = 5

# Por quanto tempo a mensagem de boas-vindas fica na tela antes de fechar.
SEGUNDOS_BOAS_VINDAS = 3.0

# Texto e cor do quadrado em cada estado (a fonte do OpenCV não tem acentos).
APARENCIA = {
    EstadoDesbloqueio.SEM_ROSTO: ("Por favor, aproxime seu rosto", tela.AMARELO),
    EstadoDesbloqueio.VARIOS_ROSTOS: ("Apenas uma pessoa por vez", tela.AMARELO),
    EstadoDesbloqueio.LONGE: ("Por favor, aproxime seu rosto", tela.AMARELO),
    EstadoDesbloqueio.DESCONHECIDO: ("Acesso negado", tela.VERMELHO),
    EstadoDesbloqueio.RECONHECENDO: ("Reconhecendo...", tela.VERDE),
    EstadoDesbloqueio.DESBLOQUEADO: ("Reconhecendo...", tela.VERDE),
}


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


def desbloquear() -> str | None:
    """Tela de bloqueio: retorna o nome de quem desbloqueou, ou None se o usuário sair."""
    desbloqueador = Desbloqueador(banco_rostos.carregar_todos())
    locutor = Locutor()

    with Camera() as camera:
        try:
            while True:
                quadro = camera.ler_quadro()
                if quadro is None:
                    return None
                avaliacao = desbloqueador.avaliar(quadro.copy())

                if avaliacao.estado in FRASES:
                    locutor.falar(FRASES[avaliacao.estado])
                mensagem, cor = APARENCIA[avaliacao.estado]
                tela.desenhar_rostos(quadro, avaliacao.rostos, cor)
                tela.escrever(quadro, "JARVIS BLOQUEADO")
                tela.escrever(quadro, mensagem, linha=1)
                tela.desenhar_progresso(quadro, avaliacao.progresso)

                if avaliacao.usuario is not None:
                    locutor.falar(f"Bem-vindo, {avaliacao.usuario.capitalize()}", interromper=True)
                    _mostrar_boas_vindas(camera, avaliacao.usuario)
                    return avaliacao.usuario
                if tela.mostrar(quadro) is tela.Acao.SAIR:
                    return None
        finally:
            tela.fechar()


def _mostrar_boas_vindas(camera: Camera, nome: str) -> None:
    """Mantém o vídeo rodando com a mensagem de boas-vindas por alguns segundos."""
    fim = time.monotonic() + SEGUNDOS_BOAS_VINDAS
    while time.monotonic() < fim:
        quadro = camera.ler_quadro()
        if quadro is None:
            return
        tela.escrever(quadro, "JARVIS DESBLOQUEADO")
        tela.escrever(quadro, f"Bem-vindo, {nome.capitalize()}!", linha=1)
        if tela.mostrar(quadro) is tela.Acao.SAIR:
            return


def _mensagem_cadastro(quantidade_rostos: int, capturadas: int) -> str:
    if quantidade_rostos == 0:
        return "Nenhum rosto. Aproxime seu rosto da camera"
    if quantidade_rostos > 1:
        return "Apenas uma pessoa por vez"
    return f"ESPACO para capturar ({capturadas}/{AMOSTRAS_CADASTRO})"
