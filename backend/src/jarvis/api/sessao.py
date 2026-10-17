"""Sessão: o Jarvis está bloqueado ou desbloqueado, e por quem.

O app manda quadros da câmera; a sessão avalia cada um e decide. A decisão
fica sempre aqui no backend, nunca no app.
"""

import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np

from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    FRASES,
    Avaliacao,
    Desbloqueador,
    EstadoDesbloqueio,
)
from jarvis.nucleo.voz import Locutor

CriarDesbloqueador = Callable[[dict[str, np.ndarray]], Desbloqueador]


class Sessao:
    """Estado da sessão. Seguro para várias requisições ao mesmo tempo."""

    def __init__(
        self,
        pasta_rostos: Path = banco_rostos.PASTA_ROSTOS,
        locutor: Locutor | None = None,
        criar_desbloqueador: CriarDesbloqueador = Desbloqueador,
    ) -> None:
        self._pasta_rostos = pasta_rostos
        self._locutor = locutor or Locutor()
        self._criar_desbloqueador = criar_desbloqueador
        self._trava = threading.Lock()
        self._usuario: str | None = None
        self._desbloqueador: Desbloqueador | None = None

    @property
    def usuario(self) -> str | None:
        """Quem desbloqueou, ou None se está bloqueado."""
        with self._trava:
            return self._usuario

    def bloquear(self) -> None:
        """Volta ao estado bloqueado. Chamar de novo quando já está bloqueado não faz mal.

        Também descarta o desbloqueador: a próxima tentativa recomeça do zero,
        com a contagem de quadros zerada e os cadastros relidos.
        """
        with self._trava:
            self._usuario = None
            self._desbloqueador = None

    def avaliar_quadro(self, quadro_bgr: np.ndarray) -> Avaliacao:
        """Avalia um quadro vindo do app. Pode levantar NenhumRostoCadastradoError."""
        with self._trava:
            if self._usuario is not None:
                return Avaliacao(EstadoDesbloqueio.DESBLOQUEADO, 1.0, self._usuario)

            if self._desbloqueador is None:
                # Carrega os cadastros a cada nova tentativa, para pegar cadastros novos.
                cadastrados = banco_rostos.carregar_todos(self._pasta_rostos)
                self._desbloqueador = self._criar_desbloqueador(cadastrados)

            avaliacao = self._desbloqueador.avaliar(quadro_bgr)

            if avaliacao.usuario is not None:
                self._usuario = avaliacao.usuario
                self._desbloqueador = None
                nome = avaliacao.usuario.capitalize()
                self._locutor.falar(f"Bem-vindo, {nome}", interromper=True)
            elif avaliacao.estado in FRASES:
                self._locutor.falar(FRASES[avaliacao.estado])
            return avaliacao
