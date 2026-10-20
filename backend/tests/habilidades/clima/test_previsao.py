import pytest

from jarvis.habilidades.clima.previsao import ClimaIndisponivelError, cartao, clima, consultar

LUGAR = {
    "results": [{"name": "Fortaleza", "admin1": "Ceará", "latitude": -3.7, "longitude": -38.5}]
}
PREVISAO = {
    "current": {
        "temperature_2m": 31.4,
        "apparent_temperature": 34.2,
        "weather_code": 0,
        "relative_humidity_2m": 50,
    },
    "daily": {
        "time": ["2026-10-20", "2026-10-21", "2026-10-22"],
        "weather_code": [51, 61, 3],
        "temperature_2m_max": [32.1, 31.0, 30.6],
        "temperature_2m_min": [25.2, 24.9, 25.0],
        "precipitation_probability_max": [20, 70, None],
    },
}


def internet_falsa(url):
    return LUGAR if "geocoding" in url else PREVISAO


def test_resume_agora_e_os_proximos_dias():
    texto = clima("Fortaleza", obter=internet_falsa)

    assert texto.splitlines() == [
        "Fortaleza (Ceará). Agora: 31 graus, sensação de 34, céu limpo, umidade 50%.",
        "Hoje: garoa fraca, máxima 32, mínima 25, chance de chuva 20%.",
        "Amanhã: chuva fraca, máxima 31, mínima 25, chance de chuva 70%.",
        "Depois de amanhã: nublado, máxima 31, mínima 25, chance de chuva ?%.",
    ]


def test_cidade_que_nao_existe():
    with pytest.raises(ClimaIndisponivelError, match="Não encontrei"):
        clima("Xyzópolis", obter=lambda url: {"results": []})


def test_pede_em_portugues_e_no_fuso_da_cidade():
    urls = []

    def anota(url):
        urls.append(url)
        return internet_falsa(url)

    clima("Fortaleza", obter=anota)

    assert "language=pt" in urls[0]
    assert "timezone=auto" in urls[1]


def test_cartao_traz_os_numeros_para_a_tela():
    dados = cartao(*consultar("Fortaleza", obter=internet_falsa))

    assert dados["tipo"] == "clima"
    assert dados["titulo"] == "Fortaleza"
    assert (dados["temperatura"], dados["sensacao"], dados["umidade"]) == (31, 34, 50)
    assert dados["ceu"] == "céu limpo"
    assert dados["dias"][1] == {
        "nome": "Amanhã",
        "ceu": "chuva fraca",
        "maxima": 31,
        "minima": 25,
        "chuva": 70,
    }
    assert dados["dias"][2]["chuva"] is None  # sem previsão de chuva: a tela mostra "?"
