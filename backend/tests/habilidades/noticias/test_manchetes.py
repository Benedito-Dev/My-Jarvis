import pytest

from jarvis.habilidades.noticias.manchetes import (
    Manchete,
    NoticiasIndisponiveisError,
    cartao,
    manchetes,
    para_a_ia,
)

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item><title>Chuva forte atinge o Ceará - G1</title><source url="x">G1</source></item>
  <item><title>Dólar fecha em queda - Valor</title><source url="x">Valor</source></item>
  <item><title>Chuva forte atinge o Ceará - G1</title><source url="x">G1</source></item>
  <item><title>Seleção vence amistoso</title></item>
  <item><title>Quarta notícia - UOL</title><source url="x">UOL</source></item>
</channel></rss>""".encode()


def test_tira_a_fonte_do_titulo_e_pula_as_repetidas():
    assert manchetes(3, obter=lambda url: FEED) == [
        Manchete("Chuva forte atinge o Ceará", "G1"),
        Manchete("Dólar fecha em queda", "Valor"),
        Manchete("Seleção vence amistoso", ""),
    ]


def test_usa_o_feed_configurado(monkeypatch):
    monkeypatch.setenv("JARVIS_NOTICIAS_RSS", "https://exemplo.com/rss")
    pedidas = []

    manchetes(obter=lambda url: pedidas.append(url) or FEED)

    assert pedidas == ["https://exemplo.com/rss"]


def test_feed_quebrado():
    with pytest.raises(NoticiasIndisponiveisError, match="quebrado"):
        manchetes(obter=lambda url: b"<html>erro")


def test_texto_para_a_ia_e_cartao():
    lista = [Manchete("Dólar fecha em queda", "Valor")]

    assert para_a_ia(lista) == "Manchetes de agora:\n- Dólar fecha em queda (Valor)"
    assert cartao(lista) == {
        "tipo": "pesquisa",
        "rotulo": "Notícias",
        "titulo": "Manchetes de hoje",
        "itens": [{"titulo": "Dólar fecha em queda", "resumo": "", "fonte": "Valor"}],
    }
