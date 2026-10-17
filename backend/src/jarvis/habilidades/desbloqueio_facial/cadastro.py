"""Lógica do cadastro: junta amostras de um rosto até dar para salvar.

Não sabe de onde vêm os quadros (janela do OpenCV ou app) nem como o progresso
é mostrado — mesma separação do `desbloqueio.py`.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import numpy as np

from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    DetectorDeRostos,
    ExtratorDeAssinaturas,
    Rosto,
    esta_perto,
)

# Várias amostras (com o rosto levemente virado) deixam o reconhecimento mais
# robusto. Mesmo número usado pelo cadastro do terminal.
AMOSTRAS_NECESSARIAS = 5


class EstadoCadastro(StrEnum):
    SEM_ROSTO = "sem_rosto"
    VARIOS_ROSTOS = "varios_rostos"
    LONGE = "longe"
    CAPTURADA = "capturada"  # a amostra entrou
    CONCLUIDO = "concluido"  # entrou a última e o rosto foi salvo


# O que o Jarvis fala em cada estado (os outros ficam em silêncio).
FRASES = {
    EstadoCadastro.SEM_ROSTO: "Por favor, aproxime seu rosto",
    EstadoCadastro.LONGE: "Por favor, aproxime seu rosto",
    EstadoCadastro.VARIOS_ROSTOS: "Apenas uma pessoa por vez",
}


@dataclass(frozen=True)
class ResultadoAmostra:
    estado: EstadoCadastro
    capturadas: int
    necessarias: int = AMOSTRAS_NECESSARIAS
    rostos: list[Rosto] = field(default_factory=list)


class Cadastro:
    """Acumula as assinaturas de uma pessoa e salva quando completa."""

    def __init__(
        self,
        nome: str,
        pasta: Path = banco_rostos.PASTA_ROSTOS,
        necessarias: int = AMOSTRAS_NECESSARIAS,
        detector: DetectorDeRostos | None = None,
        extrator: ExtratorDeAssinaturas | None = None,
    ) -> None:
        # Valida o nome já na criação: melhor recusar antes de pedir 5 fotos
        # do que depois de tirá-las.
        banco_rostos.validar_nome(nome)
        self._nome = nome
        self._pasta = pasta
        self._necessarias = necessarias
        self._detector = detector or DetectorDeRostos()
        self._extrator = extrator or ExtratorDeAssinaturas()
        self._assinaturas: list[np.ndarray] = []

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def concluido(self) -> bool:
        return len(self._assinaturas) >= self._necessarias

    def adicionar(self, quadro_bgr: np.ndarray) -> ResultadoAmostra:
        """Tenta usar este quadro como mais uma amostra. Salva ao completar."""
        rostos = self._detector.detectar(quadro_bgr)
        recusa = self._recusar(rostos, quadro_bgr.shape[1])
        if recusa is not None:
            return ResultadoAmostra(recusa, len(self._assinaturas), self._necessarias, rostos)

        self._assinaturas.append(self._extrator.extrair(quadro_bgr, rostos[0]))
        if self.concluido:
            banco_rostos.salvar(self._nome, self._assinaturas, self._pasta)
            estado = EstadoCadastro.CONCLUIDO
        else:
            estado = EstadoCadastro.CAPTURADA
        return ResultadoAmostra(estado, len(self._assinaturas), self._necessarias, rostos)

    def _recusar(self, rostos: list[Rosto], largura: int) -> EstadoCadastro | None:
        """Por que este quadro não serve, ou None se ele serve."""
        if not rostos:
            return EstadoCadastro.SEM_ROSTO
        if len(rostos) > 1:
            return EstadoCadastro.VARIOS_ROSTOS
        if not esta_perto(rostos[0], largura):
            return EstadoCadastro.LONGE
        return None
