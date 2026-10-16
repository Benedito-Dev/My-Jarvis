import numpy as np
import pytest

from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.banco_rostos import NomeInvalidoError


def test_salva_e_carrega_as_assinaturas(tmp_path):
    assinaturas = [np.full(128, 0.1, dtype=np.float32), np.full(128, 0.2, dtype=np.float32)]

    caminho = banco_rostos.salvar("Roberio", assinaturas, pasta=tmp_path)
    carregadas = banco_rostos.carregar("roberio", pasta=tmp_path)

    assert caminho == tmp_path / "roberio.npy"
    assert carregadas.shape == (2, 128)
    np.testing.assert_array_equal(carregadas, np.stack(assinaturas))


def test_pessoa_nao_cadastrada_retorna_none(tmp_path):
    assert banco_rostos.carregar("ninguem", pasta=tmp_path) is None


@pytest.mark.parametrize("nome", ["", "com espaco", "../fora", "a/b"])
def test_rejeita_nomes_inseguros(tmp_path, nome):
    with pytest.raises(NomeInvalidoError):
        banco_rostos.salvar(nome, [np.zeros(128)], pasta=tmp_path)
