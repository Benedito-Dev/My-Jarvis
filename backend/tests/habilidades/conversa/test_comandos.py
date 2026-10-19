from datetime import datetime

import pytest

from jarvis.habilidades.conversa.comandos import (
    FUSO,
    NAO_SEI,
    falar_data,
    falar_hora,
    normalizar,
    responder,
)

AGORA = datetime(2026, 10, 19, 13, 57, tzinfo=FUSO)  # uma segunda-feira


def test_normalizar_tira_acento_pontuacao_e_maiusculas():
    assert normalizar("Jarvis, que HORAS são?") == "jarvis  que horas sao"


@pytest.mark.parametrize(
    ("hora", "minuto", "esperado"),
    [
        (13, 57, "São 13 horas e 57."),
        (9, 0, "São 9 horas em ponto."),
        (12, 30, "É meio-dia e 30."),
        (0, 5, "É meia-noite e 5."),
        (1, 1, "É uma hora e 1 minuto."),
    ],
)
def test_falar_hora(hora, minuto, esperado):
    assert falar_hora(datetime(2026, 10, 19, hora, minuto)) == esperado


def test_falar_data():
    assert falar_data(AGORA) == "Hoje é segunda-feira, 19 de outubro."


@pytest.mark.parametrize(
    "frase",
    ["Que horas são?", "Jarvis, que horas são agora?", "me diz a hora", "horas"],
)
def test_entende_pedidos_de_hora(frase):
    assert responder(frase, AGORA).fala == "São 13 horas e 57."


@pytest.mark.parametrize("frase", ["Que dia é hoje?", "Qual a data de hoje?"])
def test_entende_pedidos_de_data(frase):
    assert responder(frase, AGORA).fala == "Hoje é segunda-feira, 19 de outubro."


@pytest.mark.parametrize("frase", ["Bloquear", "Jarvis, bloqueia a tela", "Pode trancar"])
def test_entende_pedidos_de_bloquear(frase):
    resposta = responder(frase, AGORA)

    assert resposta.acao == "bloquear"


def test_hora_vem_no_fuso_de_sao_paulo():
    # 15h em UTC é meio-dia em São Paulo, seja qual for o fuso da máquina.
    utc = datetime.fromisoformat("2026-10-19T15:00:00+00:00")

    assert responder("que horas são", utc).fala == "É meio-dia em ponto."


def test_o_que_nao_conhece_responde_que_ainda_nao_sabe():
    resposta = responder("abre o Spotify", AGORA)

    assert resposta.fala == NAO_SEI
    assert not resposta.entendeu
    assert resposta.acao is None


def test_sem_texto_nao_responde():
    assert responder("  ...  ", AGORA) is None
