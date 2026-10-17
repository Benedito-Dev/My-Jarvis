import cv2
import numpy as np
from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.api.cadastros import Cadastros
from jarvis.api.sessao import Sessao
from jarvis.habilidades import HABILIDADES
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.cadastro import Cadastro as CadastroDeVerdade
from jarvis.habilidades.desbloqueio_facial.cadastro import EstadoCadastro, ResultadoAmostra
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


# --- Botão Bloquear ---------------------------------------------------------------


def test_bloquear_tranca_a_sessao(tmp_path):
    cliente = cliente_com_roteiro(
        tmp_path, [Avaliacao(EstadoDesbloqueio.DESBLOQUEADO, 1.0, "benedito")]
    )
    cliente.post("/desbloqueio/quadro", content=jpeg())
    assert cliente.get("/sessao").json() == {"usuario": "Benedito"}

    resposta = cliente.post("/sessao/bloquear")

    assert resposta.status_code == 200
    assert resposta.json() == {"usuario": None}
    assert cliente.get("/sessao").json() == {"usuario": None}


def test_bloquear_sem_estar_desbloqueado_nao_quebra(tmp_path):
    cliente = cliente_com_roteiro(tmp_path, [])

    assert cliente.post("/sessao/bloquear").json() == {"usuario": None}


def test_app_instalado_pode_chamar_a_api_nos_tres_sistemas():
    # A origem do webview muda conforme o sistema (decisão 0012).
    for origem in ("tauri://localhost", "http://tauri.localhost"):
        resposta = cliente.post("/sessao/bloquear", headers={"Origin": origem})

        assert resposta.headers["access-control-allow-origin"] == origem, origem


# --- Gravar a voz -----------------------------------------------------------------


def test_gravacao_e_guardada(tmp_path):
    cliente = TestClient(criar_app(pasta_gravacoes=tmp_path))

    resposta = cliente.post(
        "/conversa/gravacao", content=b"isto seria um webm", headers={"Content-Type": "audio/webm"}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["bytes"] == len(b"isto seria um webm")
    assert corpo["arquivo"].endswith(".webm")
    assert (tmp_path / corpo["arquivo"]).read_bytes() == b"isto seria um webm"


def test_gravacao_vazia_e_recusada(tmp_path):
    cliente = TestClient(criar_app(pasta_gravacoes=tmp_path))

    assert cliente.post("/conversa/gravacao", content=b"").status_code == 400


def test_gravacao_grande_demais_e_recusada(tmp_path):
    cliente = TestClient(criar_app(pasta_gravacoes=tmp_path))

    resposta = cliente.post("/conversa/gravacao", content=b"0" * (11 * 1024 * 1024))

    assert resposta.status_code == 413


def test_gravacao_de_tipo_desconhecido_e_recusada(tmp_path):
    cliente = TestClient(criar_app(pasta_gravacoes=tmp_path))

    resposta = cliente.post(
        "/conversa/gravacao", content=b"dados", headers={"Content-Type": "text/html"}
    )

    assert resposta.status_code == 415
    assert list(tmp_path.glob("*")) == []


# --- Cadastrar rosto pelo app -----------------------------------------------------


class CadastroRoteirizado:
    """Imita o Cadastro: devolve resultados combinados, sem detectar nada."""

    def __init__(self, roteiro):
        self.roteiro = list(roteiro)
        self.concluido = False

    def adicionar(self, _quadro):
        resultado = self.roteiro.pop(0)
        self.concluido = resultado.estado is EstadoCadastro.CONCLUIDO
        return resultado


def cliente_de_cadastro(roteiro):
    cadastros = Cadastros(criar=lambda _nome: CadastroRoteirizado(roteiro))
    return TestClient(criar_app(cadastros=cadastros))


def test_amostra_boa_conta_o_progresso():
    cliente = cliente_de_cadastro([ResultadoAmostra(EstadoCadastro.CAPTURADA, 1, 5)])

    resposta = cliente.post("/cadastro/ana/amostra", content=jpeg())

    assert resposta.status_code == 200
    assert resposta.json() == {
        "estado": "capturada",
        "capturadas": 1,
        "necessarias": 5,
        "rostos": [],
    }


def test_amostra_recusada_avisa_o_motivo():
    cliente = cliente_de_cadastro([ResultadoAmostra(EstadoCadastro.SEM_ROSTO, 0, 5)])

    assert cliente.post("/cadastro/ana/amostra", content=jpeg()).json()["estado"] == "sem_rosto"


def test_ultima_amostra_conclui_o_cadastro():
    cliente = cliente_de_cadastro([ResultadoAmostra(EstadoCadastro.CONCLUIDO, 5, 5)])

    assert cliente.post("/cadastro/ana/amostra", content=jpeg()).json()["estado"] == "concluido"


def test_cadastro_de_ponta_a_ponta_salva_o_rosto(tmp_path):
    # Sem roteiro: usa o Cadastro de verdade, só com o detector e o extrator falsos.
    rosto = Rosto(topo=10, direita=400, base=300, esquerda=100)

    class Detector:
        def detectar(self, _quadro):
            return [rosto]

    class Extrator:
        def extrair(self, _quadro, _rosto):
            return np.zeros(128)

    cadastros = Cadastros(
        criar=lambda nome: CadastroDeVerdade(
            nome, pasta=tmp_path, necessarias=2, detector=Detector(), extrator=Extrator()
        )
    )
    cliente = TestClient(criar_app(pasta_rostos=tmp_path, cadastros=cadastros))

    primeira = cliente.post("/cadastro/ana/amostra", content=jpeg()).json()
    segunda = cliente.post("/cadastro/ana/amostra", content=jpeg()).json()

    assert primeira["estado"] == "capturada"
    assert segunda["estado"] == "concluido"
    assert cliente.get("/rostos").json() == {"cadastrados": ["Ana"]}


def test_nome_invalido_e_recusado():
    resposta = TestClient(criar_app()).post("/cadastro/nome%20com%20espaco/amostra", content=jpeg())

    assert resposta.status_code == 422


def test_cadastro_pela_metade_pode_ser_cancelado(tmp_path):
    rosto = Rosto(topo=10, direita=400, base=300, esquerda=100)

    class Detector:
        def detectar(self, _quadro):
            return [rosto]

    class Extrator:
        def extrair(self, _quadro, _rosto):
            return np.zeros(128)

    cadastros = Cadastros(
        criar=lambda nome: CadastroDeVerdade(
            nome, pasta=tmp_path, necessarias=3, detector=Detector(), extrator=Extrator()
        )
    )
    cliente = TestClient(criar_app(pasta_rostos=tmp_path, cadastros=cadastros))
    cliente.post("/cadastro/ana/amostra", content=jpeg())

    assert cliente.delete("/cadastro/ana").json() == {"havia": True}
    # Depois de cancelar, a contagem recomeça do zero.
    assert cliente.post("/cadastro/ana/amostra", content=jpeg()).json()["capturadas"] == 1


def test_cancelar_cadastro_que_nao_existe_nao_quebra():
    assert TestClient(criar_app()).delete("/cadastro/ninguem").json() == {"havia": False}
