import numpy as np
import pytest

from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.banco_rostos import NomeInvalidoError
from jarvis.habilidades.desbloqueio_facial.cadastro import Cadastro, EstadoCadastro
from jarvis.habilidades.desbloqueio_facial.reconhecedor import Rosto

QUADRO = np.zeros((360, 640, 3), dtype=np.uint8)

PERTO = Rosto(topo=10, direita=400, base=300, esquerda=100)  # 300px de 640 = 47%
LONGE = Rosto(topo=10, direita=150, base=90, esquerda=100)  # 50px de 640 = 8%


class DetectorFalso:
    """Devolve os rostos combinados, um conjunto por chamada."""

    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def detectar(self, _quadro):
        return self.roteiro.pop(0) if self.roteiro else []


class ExtratorFalso:
    def __init__(self):
        self.chamadas = 0

    def extrair(self, _quadro, _rosto):
        self.chamadas += 1
        return np.full(128, float(self.chamadas))


def criar(tmp_path, roteiro, nome="benedito", necessarias=3):
    extrator = ExtratorFalso()
    cadastro = Cadastro(
        nome,
        pasta=tmp_path,
        necessarias=necessarias,
        detector=DetectorFalso(roteiro),
        extrator=extrator,
    )
    return cadastro, extrator


def test_quadro_bom_vira_amostra(tmp_path):
    cadastro, _ = criar(tmp_path, [[PERTO]])

    resultado = cadastro.adicionar(QUADRO)

    assert resultado.estado is EstadoCadastro.CAPTURADA
    assert (resultado.capturadas, resultado.necessarias) == (1, 3)


def test_salva_ao_completar_as_amostras(tmp_path):
    cadastro, extrator = criar(tmp_path, [[PERTO]] * 3)

    estados = [cadastro.adicionar(QUADRO).estado for _ in range(3)]

    assert estados == [
        EstadoCadastro.CAPTURADA,
        EstadoCadastro.CAPTURADA,
        EstadoCadastro.CONCLUIDO,
    ]
    assert cadastro.concluido
    guardadas = banco_rostos.carregar("benedito", pasta=tmp_path)
    assert guardadas is not None and guardadas.shape == (3, 128)
    assert extrator.chamadas == 3


def test_sem_rosto_nao_vira_amostra(tmp_path):
    cadastro, extrator = criar(tmp_path, [[]])

    resultado = cadastro.adicionar(QUADRO)

    assert resultado.estado is EstadoCadastro.SEM_ROSTO
    assert resultado.capturadas == 0
    assert extrator.chamadas == 0


def test_varias_pessoas_no_quadro_nao_vira_amostra(tmp_path):
    cadastro, _ = criar(tmp_path, [[PERTO, PERTO]])

    assert cadastro.adicionar(QUADRO).estado is EstadoCadastro.VARIOS_ROSTOS


def test_rosto_longe_nao_vira_amostra(tmp_path):
    cadastro, _ = criar(tmp_path, [[LONGE]])

    assert cadastro.adicionar(QUADRO).estado is EstadoCadastro.LONGE


def test_quadro_ruim_no_meio_nao_perde_o_que_ja_foi_capturado(tmp_path):
    cadastro, _ = criar(tmp_path, [[PERTO], [], [PERTO]])

    cadastro.adicionar(QUADRO)
    ruim = cadastro.adicionar(QUADRO)
    depois = cadastro.adicionar(QUADRO)

    assert ruim.capturadas == 1
    assert depois.capturadas == 2


def test_nome_invalido_e_recusado_antes_de_pedir_fotos(tmp_path):
    with pytest.raises(NomeInvalidoError):
        Cadastro("nome com espaco", pasta=tmp_path)


def test_devolve_os_rostos_para_o_app_desenhar(tmp_path):
    cadastro, _ = criar(tmp_path, [[PERTO]])

    assert cadastro.adicionar(QUADRO).rostos == [PERTO]
