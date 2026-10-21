from datetime import datetime

import pytest

from jarvis.habilidades.bom_dia.resumo import (
    assuntos,
    parte_do_clima,
    parte_dos_lembretes,
    partes_das_noticias,
    saudacao,
)
from jarvis.habilidades.clima.previsao import ClimaIndisponivelError
from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.lembretes.agenda import Lembrete
from jarvis.habilidades.noticias.manchetes import NoticiasIndisponiveisError

AGORA = datetime(2026, 10, 20, 7, 30, tzinfo=FUSO)
LUGAR = {"results": [{"name": "Fortaleza", "latitude": -3.7, "longitude": -38.5}]}
PREVISAO = {
    "current": {
        "temperature_2m": 27.4,
        "apparent_temperature": 30,
        "weather_code": 0,
        "relative_humidity_2m": 70,
    },
    "daily": {
        "time": ["2026-10-20"],
        "weather_code": [1],
        "temperature_2m_max": [31.2],
        "temperature_2m_min": [24],
        "precipitation_probability_max": [10],
    },
}
FEED = b"""<rss><channel>
<item><title>Chuva forte atinge o Ceara - G1</title><source>G1</source></item>
<item><title>Dolar fecha em queda.</title></item>
</channel></rss>"""
FEED_LOCAL = b"""<rss><channel>
<item><title>Chuva forte atinge o Ceara - G1</title><source>G1</source></item>
<item><title>Fortaleza ganha novo parque - O Povo</title><source>O Povo</source></item>
</channel></rss>"""
SEM_FOTOS = b"<rss><channel></channel></rss>"


def noticias_falsas(url):
    if "bing.com" in url:
        return SEM_FOTOS
    return FEED_LOCAL if "/search" in url else FEED


def clima_falso(url):
    return LUGAR if "geocoding" in url else PREVISAO


def lembrete(hora, minuto, texto, dia=20):
    return Lembrete(1, texto, datetime(2026, 10, dia, hora, minuto, tzinfo=FUSO))


@pytest.mark.parametrize(
    ("hora", "esperado"),
    [(7, "Bom dia, Benedito."), (14, "Boa tarde, Benedito."), (21, "Boa noite, Benedito.")],
)
def test_saudacao_segue_a_hora(hora, esperado):
    assert saudacao("Benedito", AGORA.replace(hour=hora)) == esperado


def test_clima_fala_agora_e_a_maxima_de_hoje(monkeypatch):
    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")

    parte = parte_do_clima(clima_falso)

    assert parte.fala == (
        "Em Fortaleza, agora faz 27 graus, céu limpo. "
        "A máxima hoje é de 31, com 10% de chance de chuva."
    )
    assert parte.cartao["tipo"] == "clima"


def test_clima_sem_cidade_ou_fora_do_ar(monkeypatch):
    monkeypatch.delenv("JARVIS_CIDADE", raising=False)
    assert parte_do_clima(clima_falso).cartao is None

    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")

    def fora_do_ar(url):
        raise ClimaIndisponivelError("sem internet")

    parte = parte_do_clima(fora_do_ar)
    assert parte.fala == "Não consegui ver o clima agora."
    assert parte.cartao is None


def test_so_os_lembretes_de_hoje():
    pendentes = [lembrete(10, 0, "ligar pro dentista"), lembrete(9, 0, "academia", dia=21)]

    parte = parte_dos_lembretes(pendentes, AGORA)

    assert parte.fala == "Você tem um lembrete hoje: às 10, ligar pro dentista."
    assert parte.cartao["rotulo"] == "Lembretes de hoje"
    assert parte.cartao["itens"] == [{"hora": "10:00", "texto": "ligar pro dentista"}]


def test_varios_lembretes_e_nenhum():
    pendentes = [lembrete(10, 0, "dentista"), lembrete(15, 30, "reunião")]

    assert parte_dos_lembretes(pendentes, AGORA).fala == (
        "Você tem 2 lembretes hoje: às 10, dentista; e às 15 e 30, reunião."
    )
    nenhum = parte_dos_lembretes([], AGORA)
    assert nenhum.fala == "Nenhum lembrete para hoje."
    assert nenhum.cartao["titulo"] == "Nada agendado"


def test_uma_parte_por_noticia_com_a_da_regiao_no_fim(monkeypatch):
    monkeypatch.setenv("JARVIS_NOTICIAS_LOCAL", "Ceará")

    partes = partes_das_noticias(noticias_falsas)

    assert [p.fala for p in partes] == [
        "Nas notícias: Chuva forte atinge o Ceara.",
        "E mais: Dolar fecha em queda.",
        "Na sua região: Fortaleza ganha novo parque. Quer que eu detalhe alguma delas?",
    ]
    assert [p.cartao["rotulo"] for p in partes] == [
        "Notícias · Brasil",
        "Notícias · Brasil",
        "Notícias · Ceará",
    ]
    assert partes[0].cartao["tipo"] == "noticia"


def test_noticias_fora_do_ar():
    def fora_do_ar(url):
        raise NoticiasIndisponiveisError("sem internet")

    [parte] = partes_das_noticias(fora_do_ar)

    assert parte.fala == "Não consegui ler as notícias agora."
    assert parte.cartao is None


def test_assuntos_na_ordem_e_so_buscam_quando_preparados(monkeypatch):
    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")
    pedidas = []

    def clima(url):
        pedidas.append(url)
        return clima_falso(url)

    lista = assuntos(lambda: [], AGORA, clima, noticias_falsas)

    assert [a.ferramenta for a in lista] == ["clima", "listar_lembretes", "noticias"]
    assert pedidas == []
    assert lista[0].preparar()[0].cartao["tipo"] == "clima"
