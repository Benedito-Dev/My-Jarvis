"""Busca as manchetes do dia no RSS do Google Notícias, com a foto de cada uma.

Grátis e sem chave, e mais estável que a busca de notícias do DuckDuckGo.
- As do Brasil são as principais do Google Notícias (por importância). O feed
  pode ser trocado por JARVIS_NOTICIAS_RSS.
- As da sua região vêm de uma busca das últimas 24 h por JARVIS_NOTICIAS_LOCAL
  (ex.: "Ceará"); sem ela, pela cidade do clima (JARVIS_CIDADE).
- O feed do Google não traz foto: ela vem da mesma notícia no Bing Notícias,
  achada pelo título. Se o título não bater, a manchete fica sem foto (melhor
  que uma foto errada).

O acesso à internet é passado por parâmetro, para os testes.
"""

import os
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, replace

# As principais do Brasil, em português.
URL_PADRAO = "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419"
URL_BUSCA = "https://news.google.com/rss/search"
URL_FOTOS = "https://www.bing.com/news/search"
TEMPO_LIMITE_S = 10
TAMANHO_MAXIMO = 2_000_000  # um feed de manchetes tem ~100 KB; mais que isso é estranho
# Que fração das palavras do título precisa aparecer no do Bing para a foto valer.
# Outro jornal dá a mesma notícia com outras palavras ("Elmano envia Refis 2026..."
# para "Governo do Ceará propõe Refis 2026..."): metade já é a mesma notícia.
PALAVRAS_EM_COMUM = 0.5
PALAVRAS_NA_BUSCA = 8  # título longo demais, o Bing não acha nada: busca pelo começo
TAMANHO_DA_FOTO = "&w=640&h=360&c=14"  # o Bing recorta no tamanho pedido
# Só fotos servidas pelo próprio Bing: o app nunca carrega um endereço qualquer do feed.
INICIO_DA_FOTO = "https://www.bing.com/th?"


class NoticiasIndisponiveisError(RuntimeError):
    """O feed não respondeu ou veio quebrado."""


@dataclass(frozen=True)
class Manchete:
    titulo: str
    fonte: str
    imagem: str | None = None
    onde: str = "Brasil"


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


def lugar_local() -> str | None:
    """De onde vêm as notícias da região: JARVIS_NOTICIAS_LOCAL ou a cidade do clima."""
    return os.environ.get("JARVIS_NOTICIAS_LOCAL") or os.environ.get("JARVIS_CIDADE") or None


def url_local(lugar: str) -> str:
    """Busca no Google Notícias pelas notícias de `lugar` das últimas 24 h."""
    consulta = urllib.parse.urlencode(
        {"q": f"{lugar} when:1d", "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"}
    )
    return f"{URL_BUSCA}?{consulta}"


def _itens(feed: bytes) -> list[ET.Element]:
    try:
        return list(ET.fromstring(feed).iter("item"))
    except ET.ParseError as erro:
        raise NoticiasIndisponiveisError("O feed de notícias veio quebrado.") from erro


def manchetes(
    quantas: int = 3,
    obter: ObterFeed = _obter_feed,
    url: str | None = None,
    pular: tuple[str, ...] = (),
) -> list[Manchete]:
    """As `quantas` primeiras manchetes do feed, sem repetidas nem as de `pular`."""
    achadas: list[Manchete] = []
    vistos = set(pular)
    for item in _itens(obter(url or url_do_feed())):
        titulo = (item.findtext("title") or "").strip()
        fonte = (item.findtext("source") or "").strip()
        # O Google Notícias põe a fonte no fim do título: "Manchete - G1".
        if fonte and titulo.endswith(f" - {fonte}"):
            titulo = titulo.removesuffix(f" - {fonte}").strip()
        if titulo and titulo not in vistos:
            vistos.add(titulo)
            achadas.append(Manchete(titulo, fonte))
        if len(achadas) == quantas:
            break
    return achadas


def do_dia(obter: ObterFeed = _obter_feed, do_brasil: int = 2) -> list[Manchete]:
    """As do Brasil, mais uma da sua região (se houver), cada uma com a foto que achar.

    Só falha se as do Brasil falharem: sem a da região ou sem foto, segue sem elas.
    """
    lista = manchetes(do_brasil, obter=obter)
    lugar = lugar_local()
    if lugar:
        try:
            da_regiao = manchetes(
                1, obter=obter, url=url_local(lugar), pular=tuple(m.titulo for m in lista)
            )
        except NoticiasIndisponiveisError:
            da_regiao = []
        lista += [replace(m, onde=lugar) for m in da_regiao]
    # As fotos ao mesmo tempo: cada busca leva ~0,5 s.
    with ThreadPoolExecutor(max_workers=len(lista) or 1) as grupo:
        fotos = list(grupo.map(lambda m: foto(m.titulo, obter), lista))
    return [replace(m, imagem=imagem) for m, imagem in zip(lista, fotos, strict=True)]


def _palavras(titulo: str) -> set[str]:
    """As palavras que importam: minúsculas, sem pontuação e sem as curtas (de, a, em)."""
    return {p for p in re.split(r"\W+", titulo.lower()) if len(p) > 3}


def _em_comum(titulo: str, outro: str) -> float:
    """Quanto das palavras de `titulo` aparece em `outro` (de 0 a 1)."""
    palavras = _palavras(titulo)
    return len(palavras & _palavras(outro)) / len(palavras) if palavras else 0.0


def foto(titulo: str, obter: ObterFeed = _obter_feed) -> str | None:
    """A foto da mesma notícia no Bing Notícias, ou None se não achar com certeza."""
    for busca in (titulo, " ".join(titulo.split()[:PALAVRAS_NA_BUSCA])):
        consulta = urllib.parse.urlencode(
            {"q": busca, "format": "rss", "mkt": "pt-BR", "setlang": "pt-BR"}
        )
        try:
            itens = _itens(obter(f"{URL_FOTOS}?{consulta}"))
        except NoticiasIndisponiveisError:
            return None
        if itens:
            break
    for item in itens[:3]:
        if _em_comum(titulo, item.findtext("title") or "") < PALAVRAS_EM_COMUM:
            continue
        for campo in item:
            if campo.tag.endswith("}Image") and campo.text:
                endereco = campo.text.strip().replace("http://", "https://", 1)
                if endereco.startswith(INICIO_DA_FOTO):
                    return endereco + TAMANHO_DA_FOTO
    return None


def para_a_ia(lista: list[Manchete]) -> str:
    if not lista:
        return "O feed de notícias veio vazio."
    return "Manchetes de agora:\n" + "\n".join(f"- {m.titulo} ({m.fonte})" for m in lista)


def cartao(lista: list[Manchete]) -> dict:
    """Várias manchetes num cartão de pesquisa (sem resumo: o feed não traz)."""
    return {
        "tipo": "pesquisa",
        "rotulo": "Notícias",
        "titulo": "Manchetes de hoje",
        "itens": [{"titulo": m.titulo, "resumo": "", "fonte": m.fonte} for m in lista],
    }


def cartao_da_noticia(manchete: Manchete) -> dict:
    """Uma manchete só, com foto (se tiver): o bom dia mostra uma por vez."""
    return {
        "tipo": "noticia",
        "rotulo": f"Notícias · {manchete.onde}",
        "titulo": manchete.titulo,
        "fonte": manchete.fonte,
        "imagem": manchete.imagem,
    }
