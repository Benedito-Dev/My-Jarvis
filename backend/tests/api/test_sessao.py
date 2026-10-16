import numpy as np
import pytest

from jarvis.api.sessao import Sessao
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    Avaliacao,
    EstadoDesbloqueio,
    NenhumRostoCadastradoError,
)

QUADRO = np.zeros((10, 10, 3), dtype=np.uint8)


class LocutorFalso:
    def __init__(self):
        self.falas = []

    def falar(self, frase, interromper=False):
        self.falas.append((frase, interromper))
        return True


class DesbloqueadorRoteirizado:
    """Devolve avaliações numa ordem combinada."""

    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def avaliar(self, _quadro):
        return self.roteiro.pop(0)


@pytest.fixture
def pasta(tmp_path):
    banco_rostos.salvar("benedito", [np.zeros(128)], pasta=tmp_path)
    return tmp_path


def criar_sessao(pasta, roteiro):
    locutor = LocutorFalso()
    criados = []

    def criar(cadastrados):
        criados.append(cadastrados)
        return DesbloqueadorRoteirizado(roteiro)

    return Sessao(pasta, locutor=locutor, criar_desbloqueador=criar), locutor, criados


def test_comeca_bloqueada(pasta):
    sessao, _, _ = criar_sessao(pasta, [])

    assert sessao.usuario is None


def test_desbloqueia_e_da_boas_vindas(pasta):
    sessao, locutor, criados = criar_sessao(
        pasta,
        [
            Avaliacao(EstadoDesbloqueio.SEM_ROSTO, 0.0),
            Avaliacao(EstadoDesbloqueio.DESBLOQUEADO, 1.0, "benedito"),
        ],
    )

    sessao.avaliar_quadro(QUADRO)
    resultado = sessao.avaliar_quadro(QUADRO)

    assert resultado.usuario == "benedito"
    assert sessao.usuario == "benedito"
    assert list(criados[0]) == ["benedito"]  # carregou os cadastros da pasta
    assert locutor.falas == [
        ("Por favor, aproxime seu rosto", False),
        ("Bem-vindo, Benedito", True),
    ]


def test_depois_de_desbloquear_nao_reavalia(pasta):
    sessao, _, _ = criar_sessao(pasta, [Avaliacao(EstadoDesbloqueio.DESBLOQUEADO, 1.0, "benedito")])
    sessao.avaliar_quadro(QUADRO)

    resultado = sessao.avaliar_quadro(QUADRO)  # roteiro vazio: quebraria se reavaliasse

    assert resultado.estado is EstadoDesbloqueio.DESBLOQUEADO


def test_sem_cadastro_avisa(tmp_path):
    sessao = Sessao(tmp_path / "vazia", locutor=LocutorFalso())

    with pytest.raises(NenhumRostoCadastradoError):
        sessao.avaliar_quadro(QUADRO)
