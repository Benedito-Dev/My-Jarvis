import pytest

from jarvis.habilidades.pesquisa.web import (
    MAXIMO_DE_RESULTADOS,
    Achado,
    PesquisaIndisponivelError,
    _buscar_ddgs,
    para_a_ia,
    pesquisar,
)


def busca_falsa(consulta, noticias):
    tipo = "news" if noticias else "text"
    return [
        {"title": f" {tipo} {i} ", "body": "resumo " * 100, "href": f"https://x/{i}"}
        for i in range(8)
    ]


def test_pesquisa_corta_resultados_e_resumos():
    achados = pesquisar("jogo do flamengo", buscar=busca_falsa)

    assert len(achados) == MAXIMO_DE_RESULTADOS
    assert achados[0].titulo == "text 0"
    assert len(achados[0].resumo) <= 300
    assert achados[0].fonte == "https://x/0"


def test_noticias_usa_a_busca_de_noticias():
    assert pesquisar("brasil", noticias=True, buscar=busca_falsa)[0].titulo == "news 0"


def test_texto_para_a_ia():
    texto = para_a_ia([Achado("Flamengo empata", "1 a 1 com o Independiente", "ge")])

    assert texto == "- Flamengo empata: 1 a 1 com o Independiente (ge)"


def test_sem_resultados():
    assert "não encontrou" in para_a_ia([])


def test_falha_da_busca_vira_pesquisa_indisponivel(monkeypatch):
    class DDGSQuebrado:
        def text(self, *a, **k):
            raise RuntimeError("Ratelimit")

    monkeypatch.setattr("ddgs.DDGS", DDGSQuebrado)

    with pytest.raises(PesquisaIndisponivelError):
        _buscar_ddgs("x", noticias=False)
