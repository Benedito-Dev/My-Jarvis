import pytest

from jarvis.habilidades.calculadora.conta import ContaInvalidaError, calcular, formatar


@pytest.mark.parametrize(
    ("expressao", "esperado"),
    [
        ("2 + 2", 4),
        ("3480 * 17 / 100", 591.6),
        ("(1 + 2) * -3", -9),
        ("2 ** 10", 1024),
        ("3,5 x 2", 7.0),
        ("10 // 3", 3),
        ("10 % 3", 1),
    ],
)
def test_contas(expressao, esperado):
    assert calcular(expressao) == pytest.approx(esperado)


@pytest.mark.parametrize(
    "perigosa",
    ["__import__('os').system('ls')", "open('x')", "a + 1", "[1, 2]", "9 ** 99999999", "1 / 0"],
)
def test_recusa_o_que_nao_e_conta(perigosa):
    with pytest.raises(ContaInvalidaError):
        calcular(perigosa)


@pytest.mark.parametrize(("numero", "texto"), [(4.0, "4"), (591.6, "591.6"), (1 / 3, "0.333333")])
def test_formatar(numero, texto):
    assert formatar(numero) == texto
