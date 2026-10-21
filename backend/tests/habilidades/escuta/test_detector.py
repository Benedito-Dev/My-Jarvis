import numpy as np
import pytest

from jarvis.habilidades.escuta.detector import (
    BLOCO,
    JANELA,
    Classificador,
    Detector,
    EscutaIndisponivelError,
)


class Roteiro:
    """Classificador falso: devolve as notas na ordem, uma por bloco de 80 ms."""

    def __init__(self, notas):
        self.notas = list(notas)

    def __call__(self, janela):
        assert janela.shape == (JANELA, 96)
        return self.notas.pop(0) if self.notas else 0.0


def detector(notas):
    # As primeiras JANELA-1 linhas só enchem a janela: ainda não há nota.
    return Detector(lambda bloco: np.zeros(96), Roteiro(notas))


def som(blocos):
    return np.zeros(blocos * BLOCO, np.int16)


def blocos_ate_a_janela_encher():
    return JANELA - 1


def test_dispara_com_duas_notas_altas_seguidas():
    d = detector([0.1, 0.9, 0.95])
    d.ouvir(som(blocos_ate_a_janela_encher()))

    assert [d.ouvir(som(1)) for _ in range(3)] == [False, False, True]


def test_um_pico_isolado_nao_dispara():
    d = detector([0.1, 0.99, 0.1, 0.2])
    d.ouvir(som(blocos_ate_a_janela_encher()))

    assert not any(d.ouvir(som(1)) for _ in range(4))


def test_depois_de_disparar_espera_antes_de_ouvir_de_novo():
    d = detector([0.9] * 100)
    d.ouvir(som(blocos_ate_a_janela_encher()))

    disparos = [d.ouvir(som(1)) for _ in range(30)]

    assert disparos.count(True) == 2  # um logo, outro só depois da espera de 2 s
    assert disparos.index(True) == 1


def test_aceita_pedacos_de_qualquer_tamanho():
    vistos = []
    d = Detector(lambda bloco: vistos.append(len(bloco)) or np.zeros(96), Roteiro([]))

    d.ouvir(np.zeros(1000, np.int16))
    d.ouvir(np.zeros(1000, np.int16))
    d.ouvir(np.zeros(1360, np.int16))

    assert vistos == [BLOCO, BLOCO]  # 3360 amostras: dois blocos e sobram 800


def test_sem_o_treino_da_voz_a_escuta_fica_indisponivel(tmp_path):
    with pytest.raises(EscutaIndisponivelError, match="treinada"):
        Classificador(tmp_path / "nao_existe.npz")


def test_classificador_le_os_pesos_e_da_uma_chance(tmp_path):
    arquivo = tmp_path / "jarvis.npz"
    entrada = JANELA * 96
    np.savez(
        arquivo, w1=np.ones((entrada, 2)) * 0.01, b1=np.zeros(2), w2=np.ones((2, 1)), b2=[-1.0]
    )

    chance = Classificador(arquivo)(np.ones((JANELA, 96)))

    assert 0.9 < chance < 1.0
