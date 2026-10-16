"""Orquestra a habilidade: liga a entrada (câmera) à lógica e à saída (tela)."""

import time
from pathlib import Path

from jarvis.habilidades.desbloqueio_facial import banco_rostos, tela
from jarvis.habilidades.desbloqueio_facial.camera import Camera
from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    ConfirmadorDeDesbloqueio,
    DetectorDeRostos,
    ExtratorDeAssinaturas,
    esta_perto,
    identificar,
)

# Várias amostras (com o rosto levemente virado) deixam o reconhecimento mais robusto.
AMOSTRAS_CADASTRO = 5

# Por quanto tempo a mensagem de boas-vindas fica na tela antes de fechar.
SEGUNDOS_BOAS_VINDAS = 3.0


class NenhumRostoCadastradoError(RuntimeError):
    """Não dá para desbloquear sem ninguém cadastrado."""


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
    cadastrados = banco_rostos.carregar_todos()
    if not cadastrados:
        raise NenhumRostoCadastradoError(
            "Nenhum rosto cadastrado. Rode primeiro: uv run python -m jarvis cadastrar"
        )

    detector = DetectorDeRostos()
    extrator = ExtratorDeAssinaturas()
    confirmador = ConfirmadorDeDesbloqueio()

    with Camera() as camera:
        try:
            while True:
                quadro = camera.ler_quadro()
                if quadro is None:
                    return None
                limpo = quadro.copy()
                rostos = detector.detectar(quadro)

                nome_visto = None
                if len(rostos) != 1:
                    mensagem = (
                        "Por favor, aproxime seu rosto"
                        if not rostos
                        else "Apenas uma pessoa por vez"
                    )
                    tela.desenhar_rostos(quadro, rostos, tela.AMARELO)
                elif not esta_perto(rostos[0], quadro.shape[1]):
                    mensagem = "Por favor, aproxime seu rosto"
                    tela.desenhar_rostos(quadro, rostos, tela.AMARELO)
                else:
                    identificacao = identificar(extrator.extrair(limpo, rostos[0]), cadastrados)
                    nome_visto = identificacao.nome
                    if nome_visto is None:
                        mensagem = "Acesso negado"
                        tela.desenhar_rostos(quadro, rostos, tela.VERMELHO)
                    else:
                        mensagem = "Reconhecendo..."
                        tela.desenhar_rostos(quadro, rostos, tela.VERDE)

                confirmado = confirmador.registrar(nome_visto)
                tela.escrever(quadro, "JARVIS BLOQUEADO")
                tela.escrever(quadro, mensagem, linha=1)
                tela.desenhar_progresso(quadro, confirmador.progresso)

                if confirmado is not None:
                    _mostrar_boas_vindas(camera, confirmado)
                    return confirmado
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
