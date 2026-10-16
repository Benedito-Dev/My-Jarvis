import cv2
import numpy as np
from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.api.sessao import Sessao
from jarvis.habilidades import HABILIDADES
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.desbloqueio import Avaliacao, EstadoDesbloqueio
from jarvis.habilidades.desbloqueio_facial.reconhecedor import Rosto
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


# --- Desbloqueio pelo app ---------------------------------------------------------


class LocutorMudo:
    def falar(self, frase, interromper=False):
        return True


class DesbloqueadorRoteirizado:
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def avaliar(self, _quadro):
        return self.roteiro.pop(0)


def jpeg() -> bytes:
    ok, dados = cv2.imencode(".jpg", np.zeros((360, 640, 3), dtype=np.uint8))
    assert ok
    return dados.tobytes()


def cliente_com_roteiro(tmp_path, roteiro):
    banco_rostos.salvar("benedito", [np.zeros(128)], pasta=tmp_path)
    sessao = Sessao(
        tmp_path,
        locutor=LocutorMudo(),
        criar_desbloqueador=lambda _cadastrados: DesbloqueadorRoteirizado(roteiro),
    )
    return TestClient(criar_app(pasta_rostos=tmp_path, sessao=sessao))


def test_quadro_responde_estado_e_rostos(tmp_path):
    rosto = Rosto(topo=10, direita=300, base=250, esquerda=100)
    cliente = cliente_com_roteiro(
        tmp_path, [Avaliacao(EstadoDesbloqueio.RECONHECENDO, 0.4, None, [rosto])]
    )

    resposta = cliente.post(
        "/desbloqueio/quadro", content=jpeg(), headers={"Content-Type": "image/jpeg"}
    )

    assert resposta.status_code == 200
    assert resposta.json() == {
        "estado": "reconhecendo",
        "progresso": 0.4,
        "usuario": None,
        "rostos": [{"topo": 10, "direita": 300, "base": 250, "esquerda": 100}],
    }


def test_desbloqueio_aparece_na_sessao(tmp_path):
    cliente = cliente_com_roteiro(
        tmp_path, [Avaliacao(EstadoDesbloqueio.DESBLOQUEADO, 1.0, "benedito")]
    )
    assert cliente.get("/sessao").json() == {"usuario": None}

    resposta = cliente.post("/desbloqueio/quadro", content=jpeg())

    assert resposta.json()["usuario"] == "Benedito"
    assert cliente.get("/sessao").json() == {"usuario": "Benedito"}


def test_quadro_que_nao_e_imagem(tmp_path):
    cliente = cliente_com_roteiro(tmp_path, [])

    resposta = cliente.post("/desbloqueio/quadro", content=b"isso nao e uma foto")

    assert resposta.status_code == 400


def test_quadro_grande_demais(tmp_path):
    cliente = cliente_com_roteiro(tmp_path, [])

    resposta = cliente.post("/desbloqueio/quadro", content=b"0" * (3 * 1024 * 1024))

    assert resposta.status_code == 413


def test_sem_ninguem_cadastrado_responde_409(tmp_path):
    sessao = Sessao(tmp_path / "vazia", locutor=LocutorMudo())
    cliente = TestClient(criar_app(pasta_rostos=tmp_path / "vazia", sessao=sessao))

    resposta = cliente.post("/desbloqueio/quadro", content=jpeg())

    assert resposta.status_code == 409
    assert "cadastrar" in resposta.json()["detail"]
