import numpy as np
import pytest

from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    Desbloqueador,
    EstadoDesbloqueio,
    NenhumRostoCadastradoError,
)
from jarvis.habilidades.desbloqueio_facial.reconhecedor import ConfirmadorDeDesbloqueio, Rosto

QUADRO = np.zeros((360, 640, 3), dtype=np.uint8)
PERTO = Rosto(topo=50, direita=400, base=300, esquerda=200)  # 200 de 640 = 31%
LONGE = Rosto(topo=50, direita=240, base=90, esquerda=200)  # 40 de 640 = 6%

CADASTRADOS = {"benedito": np.stack([np.array([1, 0, 0], dtype=np.float32)])}
ASSINATURA_BENEDITO = np.array([1, 0, 0], dtype=np.float32)
ASSINATURA_ESTRANHA = np.array([0, 0, 1], dtype=np.float32)


class DetectorFalso:
    def __init__(self, rostos):
        self.rostos = rostos

    def detectar(self, _quadro):
        return self.rostos


class ExtratorFalso:
    def __init__(self, assinatura):
        self.assinatura = assinatura

    def extrair(self, _quadro, _rosto):
        return self.assinatura


def criar(rostos, assinatura=ASSINATURA_BENEDITO, quadros=2):
    return Desbloqueador(
        CADASTRADOS,
        detector=DetectorFalso(rostos),
        extrator=ExtratorFalso(assinatura),
        confirmador=ConfirmadorDeDesbloqueio(quadros_necessarios=quadros),
    )


def test_sem_cadastro_nao_cria():
    with pytest.raises(NenhumRostoCadastradoError):
        Desbloqueador({})


@pytest.mark.parametrize(
    ("rostos", "assinatura", "esperado"),
    [
        ([], ASSINATURA_BENEDITO, EstadoDesbloqueio.SEM_ROSTO),
        ([PERTO, PERTO], ASSINATURA_BENEDITO, EstadoDesbloqueio.VARIOS_ROSTOS),
        ([LONGE], ASSINATURA_BENEDITO, EstadoDesbloqueio.LONGE),
        ([PERTO], ASSINATURA_ESTRANHA, EstadoDesbloqueio.DESCONHECIDO),
        ([PERTO], ASSINATURA_BENEDITO, EstadoDesbloqueio.RECONHECENDO),
    ],
)
def test_estado_de_cada_situacao(rostos, assinatura, esperado):
    avaliacao = criar(rostos, assinatura, quadros=5).avaliar(QUADRO)

    assert avaliacao.estado is esperado
    assert avaliacao.usuario is None
    assert avaliacao.rostos == rostos


def test_desbloqueia_depois_de_confirmar():
    desbloqueador = criar([PERTO], quadros=2)

    primeira = desbloqueador.avaliar(QUADRO)
    segunda = desbloqueador.avaliar(QUADRO)

    assert primeira.estado is EstadoDesbloqueio.RECONHECENDO
    assert primeira.progresso == pytest.approx(0.5)
    assert segunda.estado is EstadoDesbloqueio.DESBLOQUEADO
    assert segunda.usuario == "benedito"
