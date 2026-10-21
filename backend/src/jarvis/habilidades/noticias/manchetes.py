"""Busca as manchetes do dia num feed RSS (Google Notícias, por padrão).

Grátis e sem chave, e mais estável que a busca de notícias do DuckDuckGo. O
feed pode ser trocado por JARVIS_NOTICIAS_RSS. O acesso à internet é passado
por parâmetro, para os testes.
"""

import os
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass

# As principais do Brasil, em português.
URL_PADRAO = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
TEMPO_LIMITE_S = 10
TAMANHO_MAXIMO = 2_000_000  # um feed de manchetes tem ~100 KB; mais que isso é estranho


class NoticiasIndisponiveisError(RuntimeError):
    """O feed não respondeu ou veio quebrado."""


@dataclass(frozen=True)
class Manchete:
    titulo: str
    fonte: str


ObterFeed = Callable[[str], bytes]


def _obter_feed(url: str) -> bytes:
    pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Jarvis)"})
    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
            return resposta.read(TAMANHO_MAXIMO)
    except (urllib.error.URLError, TimeoutError) as erro:
        raise NoticiasIndisponiveisError(f"O site de notícias não respondeu ({erro}).") from erro


def url_do_feed() -> str:
    return os.environ.get("JARVIS_NOTICIAS_RSS") or URL_PADRAO


def manchetes(quantas: int = 3, obter: ObterFeed = _obter_feed) -> list[Manchete]:
    """As `quantas` primeiras manchetes do feed, sem repetidas."""
    try:
        raiz = ET.fromstring(obter(url_do_feed()))
    except ET.ParseError as erro:
        raise NoticiasIndisponiveisError("O feed de notícias veio quebrado.") from erro
    achadas: list[Manchete] = []
    for item in raiz.iter("item"):
        titulo = (item.findtext("title") or "").strip()
        fonte = (item.findtext("source") or "").strip()
        # O Google Notícias põe a fonte no fim do título: "Manchete - G1".
        if fonte and titulo.endswith(f" - {fonte}"):
            titulo = titulo.removesuffix(f" - {fonte}").strip()
        if titulo and all(m.titulo != titulo for m in achadas):
            achadas.append(Manchete(titulo, fonte))
        if len(achadas) == quantas:
            break
    return achadas


def para_a_ia(lista: list[Manchete]) -> str:
    if not lista:
        return "O feed de notícias veio vazio."
    return "Manchetes de agora:\n" + "\n".join(f"- {m.titulo} ({m.fonte})" for m in lista)


def cartao(lista: list[Manchete]) -> dict:
    """As manchetes no cartão de pesquisa da tela (sem resumo: o feed não traz)."""
    return {
        "tipo": "pesquisa",
        "rotulo": "Notícias",
        "titulo": "Manchetes de hoje",
        "itens": [{"titulo": m.titulo, "resumo": "", "fonte": m.fonte} for m in lista],
    }
