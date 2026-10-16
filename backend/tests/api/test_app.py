import numpy as np
from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.habilidades import HABILIDADES
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.nucleo.config import NOME_ASSISTENTE

cliente = TestClient(criar_app())


def test_status_retorna_nome_versao_e_habilidades():
    resposta = cliente.get("/status")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == NOME_ASSISTENTE
    assert corpo["versao"]
    assert [h["id"] for h in corpo["habilidades"]] == [h.id for h in HABILIDADES]
    assert {h["situacao"] for h in corpo["habilidades"]} <= {"pronta", "em_breve"}


def test_app_em_desenvolvimento_pode_chamar_a_api():
    resposta = cliente.get("/status", headers={"Origin": "http://localhost:1420"})

    assert resposta.headers["access-control-allow-origin"] == "http://localhost:1420"


def test_site_qualquer_nao_pode_chamar_a_api():
    resposta = cliente.get("/status", headers={"Origin": "https://site-malicioso.com"})

    assert "access-control-allow-origin" not in resposta.headers


def test_rostos_lista_os_cadastrados_com_nome_para_exibir(tmp_path):
    banco_rostos.salvar("benedito", [np.zeros(128)], pasta=tmp_path)
    banco_rostos.salvar("ana", [np.zeros(128)], pasta=tmp_path)

    resposta = TestClient(criar_app(pasta_rostos=tmp_path)).get("/rostos")

    assert resposta.json() == {"cadastrados": ["Ana", "Benedito"]}


def test_rostos_sem_ninguem_cadastrado(tmp_path):
    resposta = TestClient(criar_app(pasta_rostos=tmp_path / "vazia")).get("/rostos")

    assert resposta.json() == {"cadastrados": []}
