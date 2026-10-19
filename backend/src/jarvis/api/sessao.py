"""Sessão: o Jarvis está bloqueado ou desbloqueado, e por quem.

O app manda quadros da câmera; a sessão avalia cada um e decide. A decisão
fica sempre aqui no backend, nunca no app.
"""

import functools
import threading
import time
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
from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    DetectorDeRostos,
    ExtratorDeAssinaturas,
)
from jarvis.nucleo.acesso_pin import AcessoPin
from jarvis.nucleo.voz import Locutor

CriarDesbloqueador = Callable[[dict[str, np.ndarray]], Desbloqueador]
MAXIMO_TENTATIVAS_PIN = 5
TEMPO_BLOQUEIO_PIN_S = 30


@functools.cache
def modelos() -> tuple[DetectorDeRostos, ExtratorDeAssinaturas]:
    """Carrega os modelos de visão uma vez só (leva ~2 s).

    Bloquear descarta o desbloqueador para zerar a contagem, mas os modelos não
    mudam: recarregá-los a cada bloqueio atrasava o primeiro quadro em 2 s.
    """
    return DetectorDeRostos(), ExtratorDeAssinaturas()


def desbloqueador_com_modelos_prontos(cadastrados: dict[str, np.ndarray]) -> Desbloqueador:
    if not cadastrados:
        # Levanta NenhumRostoCadastradoError sem gastar 2 s carregando modelos.
        return Desbloqueador(cadastrados)
    detector, extrator = modelos()
    return Desbloqueador(cadastrados, detector=detector, extrator=extrator)


class PinTemporariamenteBloqueadoError(RuntimeError):
    """O limite de tentativas do acesso alternativo foi atingido."""

    def __init__(self, restante_s: int) -> None:
        super().__init__("Muitas tentativas. Aguarde antes de tentar novamente.")
        self.restante_s = restante_s


class CredenciaisPinInvalidasError(RuntimeError):
    """Identificador ou PIN não conferem, sem revelar qual dos dois falhou."""


class Sessao:
    """Estado da sessão. Seguro para várias requisições ao mesmo tempo."""

    def __init__(
        self,
        pasta_rostos: Path = banco_rostos.PASTA_ROSTOS,
        locutor: Locutor | None = None,
        criar_desbloqueador: CriarDesbloqueador = desbloqueador_com_modelos_prontos,
    ) -> None:
        self._pasta_rostos = pasta_rostos
        self._locutor = locutor or Locutor()
        self._criar_desbloqueador = criar_desbloqueador
        self._trava = threading.Lock()
        self._usuario: str | None = None
        self._desbloqueador: Desbloqueador | None = None
        self._falhas_pin = 0
        self._pin_bloqueado_ate = 0.0

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
            self._falhas_pin = 0
            self._pin_bloqueado_ate = 0.0

    def desbloquear_por_pin(self, identificador: str, pin: str, acesso_pin: AcessoPin) -> str:
        """Valida o acesso alternativo sem expor a lista de perfis."""
        with self._trava:
            if self._usuario is not None:
                return self._usuario

            agora = time.monotonic()
            if agora < self._pin_bloqueado_ate:
                restante = max(1, int(self._pin_bloqueado_ate - agora))
                raise PinTemporariamenteBloqueadoError(restante)

            usuario = acesso_pin.autenticar(identificador, pin)
            if usuario is None:
                self._falhas_pin += 1
                if self._falhas_pin >= MAXIMO_TENTATIVAS_PIN:
                    self._pin_bloqueado_ate = agora + TEMPO_BLOQUEIO_PIN_S
                    self._falhas_pin = 0
                    raise PinTemporariamenteBloqueadoError(TEMPO_BLOQUEIO_PIN_S)
                raise CredenciaisPinInvalidasError

            self._falhas_pin = 0
            self._pin_bloqueado_ate = 0.0
            self._usuario = usuario
            self._desbloqueador = None
            self._locutor.falar(f"Bem-vindo, {usuario.capitalize()}", interromper=True)
            return usuario

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
