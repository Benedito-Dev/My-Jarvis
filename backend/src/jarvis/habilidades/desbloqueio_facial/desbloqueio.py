"""Lógica do desbloqueio: olha UM quadro e diz em que pé está.

Não sabe de onde vem o quadro (webcam local ou app) nem como o resultado é
mostrado. Por isso serve tanto à janela do OpenCV quanto à API.
"""

from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np

from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    ConfirmadorDeDesbloqueio,
    DetectorDeRostos,
    ExtratorDeAssinaturas,
    Rosto,
    esta_perto,
    identificar,
)


class NenhumRostoCadastradoError(RuntimeError):
    """Não dá para desbloquear sem ninguém cadastrado."""


class EstadoDesbloqueio(StrEnum):
    SEM_ROSTO = "sem_rosto"
    VARIOS_ROSTOS = "varios_rostos"
    LONGE = "longe"
    DESCONHECIDO = "desconhecido"
    RECONHECENDO = "reconhecendo"
    DESBLOQUEADO = "desbloqueado"


# O que o Jarvis fala em voz alta em cada estado (os outros ficam em silêncio).
FRASES = {
    EstadoDesbloqueio.SEM_ROSTO: "Por favor, aproxime seu rosto",
    EstadoDesbloqueio.LONGE: "Por favor, aproxime seu rosto",
    EstadoDesbloqueio.DESCONHECIDO: "Acesso negado",
}


@dataclass(frozen=True)
class Avaliacao:
    estado: EstadoDesbloqueio
    progresso: float  # de 0 a 1, quanto falta para confirmar
    usuario: str | None = None  # preenchido só quando DESBLOQUEADO
    rostos: list[Rosto] = field(default_factory=list)


class Desbloqueador:
    """Avalia quadro a quadro até alguém cadastrado ser confirmado."""

    def __init__(
        self,
        cadastrados: dict[str, np.ndarray],
        detector: DetectorDeRostos | None = None,
        extrator: ExtratorDeAssinaturas | None = None,
        confirmador: ConfirmadorDeDesbloqueio | None = None,
    ) -> None:
        if not cadastrados:
            raise NenhumRostoCadastradoError(
                "Nenhum rosto cadastrado. Rode primeiro: uv run python -m jarvis cadastrar"
            )
        self._cadastrados = cadastrados
        self._detector = detector or DetectorDeRostos()
        self._extrator = extrator or ExtratorDeAssinaturas()
        self._confirmador = confirmador or ConfirmadorDeDesbloqueio()

    def avaliar(self, quadro_bgr: np.ndarray) -> Avaliacao:
        rostos = self._detector.detectar(quadro_bgr)
        estado, nome_visto = self._classificar(quadro_bgr, rostos)

        confirmado = self._confirmador.registrar(nome_visto)
        if confirmado is not None:
            return Avaliacao(EstadoDesbloqueio.DESBLOQUEADO, 1.0, confirmado, rostos)
        return Avaliacao(estado, self._confirmador.progresso, None, rostos)

    def _classificar(
        self, quadro_bgr: np.ndarray, rostos: list[Rosto]
    ) -> tuple[EstadoDesbloqueio, str | None]:
        if not rostos:
            return EstadoDesbloqueio.SEM_ROSTO, None
        if len(rostos) > 1:
            return EstadoDesbloqueio.VARIOS_ROSTOS, None
        if not esta_perto(rostos[0], quadro_bgr.shape[1]):
            return EstadoDesbloqueio.LONGE, None

        identificacao = identificar(
            self._extrator.extrair(quadro_bgr, rostos[0]), self._cadastrados
        )
        if identificacao.nome is None:
            return EstadoDesbloqueio.DESCONHECIDO, None
        return EstadoDesbloqueio.RECONHECENDO, identificacao.nome
