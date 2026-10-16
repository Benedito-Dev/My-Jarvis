from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.habilidades import HABILIDADES

cliente = TestClient(criar_app())


def test_status_retorna_nome_versao_e_habilidades():
    resposta = cliente.get("/status")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "J.A.R.V.I.S."
    assert corpo["versao"]
    assert [h["id"] for h in corpo["habilidades"]] == [h.id for h in HABILIDADES]


def test_app_em_desenvolvimento_pode_chamar_a_api():
    resposta = cliente.get("/status", headers={"Origin": "http://localhost:1420"})

    assert resposta.headers["access-control-allow-origin"] == "http://localhost:1420"


def test_site_qualquer_nao_pode_chamar_a_api():
    resposta = cliente.get("/status", headers={"Origin": "https://site-malicioso.com"})

    assert "access-control-allow-origin" not in resposta.headers
