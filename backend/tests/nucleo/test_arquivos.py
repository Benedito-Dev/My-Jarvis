import hashlib

import pytest

from jarvis.nucleo.arquivos import ArquivoCorrompidoError, baixar_se_necessario


@pytest.fixture
def origem(tmp_path):
    arquivo = tmp_path / "origem.bin"
    arquivo.write_bytes(b"modelo de mentira")
    return arquivo


def sha(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo).hexdigest()


def test_baixa_e_confere_o_hash(tmp_path, origem):
    destino = tmp_path / "modelos" / "modelo.onnx"

    resultado = baixar_se_necessario(origem.as_uri(), destino, sha(b"modelo de mentira"))

    assert resultado == destino
    assert destino.read_bytes() == b"modelo de mentira"


def test_hash_errado_nao_deixa_arquivo(tmp_path, origem):
    destino = tmp_path / "modelo.onnx"

    with pytest.raises(ArquivoCorrompidoError):
        baixar_se_necessario(origem.as_uri(), destino, sha(b"outro conteudo"))

    assert list(tmp_path.glob("modelo.onnx*")) == []  # nem o final, nem o .parcial


def test_nao_baixa_de_novo_se_ja_existe(tmp_path):
    destino = tmp_path / "modelo.onnx"
    destino.write_bytes(b"ja estava aqui")

    baixar_se_necessario("file:///nao/existe", destino, "qualquer")

    assert destino.read_bytes() == b"ja estava aqui"
