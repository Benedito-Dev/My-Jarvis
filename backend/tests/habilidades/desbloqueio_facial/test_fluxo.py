from jarvis.habilidades.desbloqueio_facial.fluxo import AMOSTRAS_CADASTRO, _mensagem_cadastro


def test_mensagens_do_cadastro():
    assert "Aproxime" in _mensagem_cadastro(quantidade_rostos=0, capturadas=0)
    assert "uma pessoa" in _mensagem_cadastro(quantidade_rostos=2, capturadas=0)
    assert f"(3/{AMOSTRAS_CADASTRO})" in _mensagem_cadastro(quantidade_rostos=1, capturadas=3)
