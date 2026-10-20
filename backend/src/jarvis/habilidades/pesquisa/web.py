"""Busca na web pelo DuckDuckGo (biblioteca `ddgs`): grátis e sem chave.

Devolve só títulos e resumos curtos; quem transforma isso em resposta falada
é a IA. A busca de verdade é passada por parâmetro, para os testes não irem à
internet.
"""

from collections.abc import Callable
from dataclasses import dataclass

MAXIMO_DE_RESULTADOS = 5
REGIAO = "br-pt"  # resultados em português, do Brasil primeiro


@dataclass(frozen=True)
class Achado:
    titulo: str
    resumo: str
    fonte: str


class PesquisaIndisponivelError(RuntimeError):
    """A busca falhou (sem internet, ou o serviço recusou)."""


# (consulta, noticias?) -> lista de dicionários como o ddgs devolve
Buscar = Callable[[str, bool], list[dict]]


def _buscar_ddgs(consulta: str, noticias: bool) -> list[dict]:
    from ddgs import DDGS  # import só quando pesquisar

    try:
        cliente = DDGS()
        if noticias:
            return cliente.news(consulta, region=REGIAO, max_results=MAXIMO_DE_RESULTADOS)
        return cliente.text(consulta, region=REGIAO, max_results=MAXIMO_DE_RESULTADOS)
    except Exception as erro:  # o ddgs levanta vários tipos; para nós é tudo "não deu"
        raise PesquisaIndisponivelError(str(erro)) from erro


def pesquisar(consulta: str, noticias: bool = False, buscar: Buscar = _buscar_ddgs) -> list[Achado]:
    """Os primeiros resultados para `consulta` (ou só notícias, se `noticias`)."""
    achados = []
    for item in buscar(consulta, noticias)[:MAXIMO_DE_RESULTADOS]:
        achados.append(
            Achado(
                titulo=(item.get("title") or "").strip(),
                resumo=(item.get("body") or item.get("excerpt") or "").strip()[:300],
                fonte=item.get("source") or item.get("href") or item.get("url") or "",
            )
        )
    return achados


def para_a_ia(achados: list[Achado]) -> str:
    """Os achados num texto compacto, para a IA ler e responder."""
    if not achados:
        return "A busca não encontrou nada."
    return "\n".join(f"- {a.titulo}: {a.resumo} ({a.fonte})" for a in achados)
