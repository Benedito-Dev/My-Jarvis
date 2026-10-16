from jarvis.__main__ import saudacao


def test_saudacao():
    assert saudacao() == "Olá, eu sou o Jarvis"
