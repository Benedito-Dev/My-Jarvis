from xml.sax.saxutils import escape

import pytest

from jarvis.habilidades.noticias.manchetes import (
    Manchete,
    NoticiasIndisponiveisError,
    cartao,
    cartao_da_noticia,
    do_dia,
    foto,
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


def bing(*itens):
    """Um feed do Bing Notícias com (título, foto) em cada item."""
    corpo = "".join(
        f"<item><title>{titulo}</title><n:Image>{escape(imagem)}</n:Image></item>"
        for titulo, imagem in itens
    )
    return f'<rss xmlns:n="https://bing"><channel>{corpo}</channel></rss>'.encode()


FOTO = "http://www.bing.com/th?id=OVFT.abc&pid=News"


def test_foto_da_mesma_noticia_mesmo_com_outras_palavras():
    feed = bing(
        ("Prazo do IPVA termina no dia 30", "http://www.bing.com/th?id=OUTRA&pid=News"),
        ("Elmano envia Refis 2026 com descontos de até 100% em multas e juros", FOTO),
    )

    titulo = "Refis 2026: Governo do Ceará propõe descontos de até 100% em multas e juros"

    endereco = foto(titulo, obter=lambda url: feed)

    assert endereco == "https://www.bing.com/th?id=OVFT.abc&pid=News&w=640&h=360&c=14"


def test_sem_foto_quando_o_titulo_nao_bate():
    feed = bing(("Seleção vence amistoso em Londres", FOTO))

    assert foto("Dólar fecha em queda com juros", obter=lambda url: feed) is None


def test_so_aceita_foto_do_proprio_bing():
    feed = bing(("Dólar fecha em queda", "https://site-estranho.com/x.jpg"))

    assert foto("Dólar fecha em queda", obter=lambda url: feed) is None


def test_titulo_longo_sem_resultado_tenta_pelo_comeco():
    pedidas = []

    def obter(url):
        pedidas.append(url)
        return (
            bing()
            if len(pedidas) == 1
            else bing(("Um dois três quatro cinco seis sete oito nove", FOTO))
        )

    titulo = "Um dois três quatro cinco seis sete oito nove dez onze doze"

    assert foto(titulo, obter=obter)
    assert len(pedidas) == 2
    assert "nove" not in pedidas[1]


def test_do_dia_traz_duas_do_brasil_e_uma_da_regiao(monkeypatch):
    monkeypatch.setenv("JARVIS_NOTICIAS_LOCAL", "Ceará")
    local = """<rss><channel>
    <item><title>Chuva forte atinge o Ceará - G1</title><source>G1</source></item>
    <item><title>Fortaleza ganha parque - O Povo</title><source>O Povo</source></item>
    </channel></rss>""".encode()

    def obter(url):
        if "bing.com" in url:
            return bing(("Chuva forte atinge o Ceará", FOTO))
        return local if "Cear%C3%A1+when%3A1d" in url else FEED

    lista = do_dia(obter)

    assert [(m.titulo, m.onde) for m in lista] == [
        ("Chuva forte atinge o Ceará", "Brasil"),
        ("Dólar fecha em queda", "Brasil"),
        ("Fortaleza ganha parque", "Ceará"),  # a repetida do Brasil é pulada
    ]
    assert lista[0].imagem and lista[1].imagem is None


def test_do_dia_sem_regiao_configurada_traz_so_as_do_brasil():
    assert [m.onde for m in do_dia(lambda url: FEED if "google" in url else bing())] == [
        "Brasil",
        "Brasil",
    ]


def test_cartao_de_uma_noticia():
    manchete = Manchete("Dólar fecha em queda", "Valor", "https://www.bing.com/th?id=x", "Ceará")

    assert cartao_da_noticia(manchete) == {
        "tipo": "noticia",
        "rotulo": "Notícias · Ceará",
        "titulo": "Dólar fecha em queda",
        "fonte": "Valor",
        "imagem": "https://www.bing.com/th?id=x",
    }
