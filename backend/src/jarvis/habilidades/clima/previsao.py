"""Busca o clima de uma cidade na Open-Meteo e resume para a IA.

Grátis e sem chave. A cidade padrão vem de JARVIS_CIDADE; sem ela, a IA
pergunta. O acesso à internet é passado por parâmetro, para os testes.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

URL_LUGAR = "https://geocoding-api.open-meteo.com/v1/search"
URL_PREVISAO = "https://api.open-meteo.com/v1/forecast"
TEMPO_LIMITE_S = 10

# Códigos de tempo da OMM (WMO) que a Open-Meteo usa.
CEU = {
    0: "céu limpo",
    1: "quase limpo",
    2: "parcialmente nublado",
    3: "nublado",
    45: "neblina",
    48: "neblina com geada",
    51: "garoa fraca",
    53: "garoa",
    55: "garoa forte",
    61: "chuva fraca",
    63: "chuva",
    65: "chuva forte",
    66: "chuva congelante",
    67: "chuva congelante forte",
    71: "neve fraca",
    73: "neve",
    75: "neve forte",
    80: "pancadas de chuva fracas",
    81: "pancadas de chuva",
    82: "pancadas de chuva fortes",
    95: "trovoadas",
    96: "trovoadas com granizo",
    99: "trovoadas fortes com granizo",
}
DIAS = ["Hoje", "Amanhã", "Depois de amanhã"]


class ClimaIndisponivelError(RuntimeError):
    """Cidade não encontrada ou serviço fora do ar."""


@dataclass(frozen=True)
class Lugar:
    nome: str
    estado: str
    latitude: float
    longitude: float


ObterJson = Callable[[str], dict]


def _obter_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=TEMPO_LIMITE_S) as resposta:
            return json.load(resposta)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        raise ClimaIndisponivelError(f"O serviço de clima não respondeu ({erro}).") from erro


def cidade_padrao() -> str | None:
    return os.environ.get("JARVIS_CIDADE") or None


def encontrar(cidade: str, obter: ObterJson = _obter_json) -> Lugar:
    consulta = urllib.parse.urlencode({"name": cidade, "count": 1, "language": "pt"})
    resultados = obter(f"{URL_LUGAR}?{consulta}").get("results") or []
    if not resultados:
        raise ClimaIndisponivelError(f"Não encontrei a cidade {cidade!r}.")
    r = resultados[0]
    return Lugar(r["name"], r.get("admin1", ""), r["latitude"], r["longitude"])


def consultar(cidade: str, obter: ObterJson = _obter_json) -> tuple[Lugar, dict]:
    """O lugar e os dados da Open-Meteo: agora e os próximos 3 dias em `cidade`."""
    lugar = encontrar(cidade, obter)
    consulta = urllib.parse.urlencode(
        {
            "latitude": lugar.latitude,
            "longitude": lugar.longitude,
            "current": "temperature_2m,apparent_temperature,weather_code,relative_humidity_2m",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,"
            "precipitation_probability_max",
            "timezone": "auto",
            "forecast_days": 3,
        }
    )
    return lugar, obter(f"{URL_PREVISAO}?{consulta}")


def clima(cidade: str, obter: ObterJson = _obter_json) -> str:
    """Agora e os próximos 3 dias em `cidade`, num texto curto para a IA."""
    return resumir(*consultar(cidade, obter))


def resumir(lugar: Lugar, dados: dict) -> str:
    agora = dados["current"]
    linhas = [
        f"{lugar.nome} ({lugar.estado}). Agora: {round(agora['temperature_2m'])} graus, "
        f"sensação de {round(agora['apparent_temperature'])}, "
        f"{CEU.get(agora['weather_code'], 'tempo indefinido')}, "
        f"umidade {agora['relative_humidity_2m']}%."
    ]
    dia = dados["daily"]
    for i, nome in enumerate(DIAS[: len(dia["time"])]):
        chuva = dia["precipitation_probability_max"][i]
        linhas.append(
            f"{nome}: {CEU.get(dia['weather_code'][i], 'tempo indefinido')}, "
            f"máxima {round(dia['temperature_2m_max'][i])}, "
            f"mínima {round(dia['temperature_2m_min'][i])}, "
            f"chance de chuva {chuva if chuva is not None else '?'}%."
        )
    return "\n".join(linhas)


def cartao(lugar: Lugar, dados: dict) -> dict:
    """O mesmo clima, para o cartão na tela (números, não frases)."""
    agora = dados["current"]
    dia = dados["daily"]
    return {
        "tipo": "clima",
        "rotulo": "Clima · agora",
        "titulo": lugar.nome,
        "temperatura": round(agora["temperature_2m"]),
        "sensacao": round(agora["apparent_temperature"]),
        "umidade": agora["relative_humidity_2m"],
        "ceu": CEU.get(agora["weather_code"], "tempo indefinido"),
        "dias": [
            {
                "nome": nome,
                "ceu": CEU.get(dia["weather_code"][i], "tempo indefinido"),
                "maxima": round(dia["temperature_2m_max"][i]),
                "minima": round(dia["temperature_2m_min"][i]),
                "chuva": dia["precipitation_probability_max"][i],
            }
            for i, nome in enumerate(DIAS[: len(dia["time"])])
        ],
    }
