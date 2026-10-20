import cv2
import numpy as np
from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.api.cadastros import Cadastros
from jarvis.api.sessao import Sessao
from jarvis.habilidades import HABILIDADES
from jarvis.habilidades.conversa.cerebro import CerebroIndisponivelError
from jarvis.habilidades.conversa.transcricao import TranscricaoIndisponivelError
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.cadastro import Cadastro as CadastroDeVerdade
from jarvis.habilidades.desbloqueio_facial.cadastro import EstadoCadastro, ResultadoAmostra
from jarvis.habilidades.desbloqueio_facial.desbloqueio import Avaliacao, EstadoDesbloqueio
from jarvis.habilidades.desbloqueio_facial.reconhecedor import Rosto
from jarvis.nucleo.acesso_pin import AcessoPin
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

    acesso_pin = AcessoPin(tmp_path / "acesso_pin.json")
    acesso_pin.configurar("benedito", "benedito", "123456")
    cliente = TestClient(criar_app(pasta_rostos=tmp_path, acesso_pin=acesso_pin))
    cliente.post("/sessao/pin", json={"identificador": "benedito", "pin": "123456"})

    resposta = cliente.get("/rostos")

    assert resposta.json() == {"cadastrados": ["Ana", "Benedito"]}


def test_rostos_sem_ninguem_cadastrado(tmp_path):
    acesso_pin = AcessoPin(tmp_path / "acesso_pin.json")
    acesso_pin.configurar("benedito", "benedito", "123456")
    cliente = TestClient(criar_app(pasta_rostos=tmp_path / "vazia", acesso_pin=acesso_pin))
    cliente.post("/sessao/pin", json={"identificador": "benedito", "pin": "123456"})

    resposta = cliente.get("/rostos")

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
        # Este rosto foi montado à mão, sem a linha do YuNet, então não tem pontos.
        "rostos": [{"topo": 10, "direita": 300, "base": 250, "esquerda": 100, "pontos": []}],
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


class TranscritorFalso:
    """Responde sempre a mesma frase: os testes não carregam o Whisper de verdade."""

    def __init__(self, texto="que horas são"):
        self.texto = texto
        self.ouvidos = []

    def transcrever(self, audio):
        self.ouvidos.append(audio)
        return self.texto


class TranscritorSemModelo:
    def transcrever(self, _audio):
        raise TranscricaoIndisponivelError("Não consegui carregar o modelo de transcrição.")


class LocutorQueAnota:
    """Não fala de verdade: só anota o que o Jarvis teria dito."""

    def __init__(self):
        self.frases = []

    def falar(self, frase, interromper=False):
        self.frases.append(frase)
        return True


class CerebroFalso:
    def __init__(self, fala="Um omelete resolve.", erro=None):
        self.fala = fala
        self.erro = erro
        self.perguntas = []

    def responder(self, pergunta, usuario):
        self.perguntas.append((pergunta, usuario))
        if self.erro:
            raise self.erro
        return self.fala


def cliente_de_gravacao(pasta, transcritor=None, sessao=None, cerebro=None):
    sessao = sessao or Sessao(pasta / "rostos", locutor=LocutorQueAnota())
    return TestClient(
        criar_app(
            pasta_gravacoes=pasta,
            transcritor=transcritor or TranscritorFalso(),
            sessao=sessao,
            cerebro=cerebro,
        )
    )


def sessao_aberta(pasta, locutor=None):
    sessao = Sessao(pasta / "rostos", locutor=locutor or LocutorQueAnota())
    sessao._usuario = "benedito"  # como se já tivesse desbloqueado
    return sessao


def test_gravacao_e_guardada(tmp_path):
    cliente = cliente_de_gravacao(tmp_path)

    resposta = cliente.post(
        "/conversa/gravacao", content=b"isto seria um webm", headers={"Content-Type": "audio/webm"}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["bytes"] == len(b"isto seria um webm")
    assert corpo["arquivo"].endswith(".webm")
    assert (tmp_path / corpo["arquivo"]).read_bytes() == b"isto seria um webm"


def test_gravacao_volta_com_o_que_foi_dito(tmp_path):
    transcritor = TranscritorFalso("que horas são")
    cliente = cliente_de_gravacao(tmp_path, transcritor)

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["texto"] == "que horas são"
    assert transcritor.ouvidos == [tmp_path / corpo["arquivo"]]


def test_pergunta_a_hora_e_o_jarvis_responde_em_voz(tmp_path):
    locutor = LocutorQueAnota()
    sessao = Sessao(tmp_path / "rostos", locutor=locutor)
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("Que horas são?"), sessao)

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["resposta"].startswith(("São", "É"))
    assert corpo["acao"] is None
    assert locutor.frases == [corpo["resposta"]]


def test_pedir_para_bloquear_bloqueia_a_sessao(tmp_path):
    sessao = Sessao(tmp_path / "rostos", locutor=LocutorQueAnota())
    sessao._usuario = "benedito"  # como se já tivesse desbloqueado
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("Jarvis, bloquear"), sessao)

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["acao"] == "bloquear"
    assert sessao.usuario is None


def test_pedido_desconhecido_responde_que_ainda_nao_sabe(tmp_path):
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("abre o Spotify"))

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["resposta"] == "Ainda não sei fazer isso."


def test_pergunta_livre_vai_para_o_cerebro_e_e_falada(tmp_path):
    locutor = LocutorQueAnota()
    cerebro = CerebroFalso("Um omelete resolve.")
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("ideia de jantar?"), sessao_aberta(tmp_path, locutor), cerebro
    )

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["resposta"] == "Um omelete resolve."
    assert cerebro.perguntas == [("ideia de jantar?", "Benedito")]
    assert locutor.frases == ["Um omelete resolve."]


def test_comando_conhecido_nao_gasta_a_ia(tmp_path):
    cerebro = CerebroFalso()
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("que horas são"), sessao_aberta(tmp_path), cerebro
    )

    cliente.post("/conversa/gravacao", content=b"voz")

    assert cerebro.perguntas == []


def test_com_o_jarvis_bloqueado_a_ia_nao_e_usada(tmp_path):
    cerebro = CerebroFalso()
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("ideia de jantar?"), cerebro=cerebro)

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert cerebro.perguntas == []
    assert corpo["resposta"] == "Ainda não sei fazer isso."


def test_ia_fora_do_ar_avisa_em_voz(tmp_path):
    cerebro = CerebroFalso(erro=CerebroIndisponivelError("sem crédito"))
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("ideia de jantar?"), sessao_aberta(tmp_path), cerebro
    )

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["resposta"].startswith("Não consegui pensar nisso agora")


def test_sem_fala_nao_responde_nada(tmp_path):
    locutor = LocutorQueAnota()
    sessao = Sessao(tmp_path / "rostos", locutor=locutor)
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso(""), sessao)

    corpo = cliente.post("/conversa/gravacao", content=b"voz").json()

    assert corpo["resposta"] is None
    assert locutor.frases == []


def test_sem_modelo_de_transcricao_responde_503(tmp_path):
    cliente = cliente_de_gravacao(tmp_path, TranscritorSemModelo())

    resposta = cliente.post("/conversa/gravacao", content=b"voz")

    assert resposta.status_code == 503
    assert "transcrição" in resposta.json()["detail"]


def test_gravacao_vazia_e_recusada(tmp_path):
    cliente = cliente_de_gravacao(tmp_path)

    assert cliente.post("/conversa/gravacao", content=b"").status_code == 400


def test_gravacao_grande_demais_e_recusada(tmp_path):
    cliente = cliente_de_gravacao(tmp_path)

    resposta = cliente.post("/conversa/gravacao", content=b"0" * (11 * 1024 * 1024))

    assert resposta.status_code == 413


def test_gravacao_de_tipo_desconhecido_e_recusada(tmp_path):
    cliente = cliente_de_gravacao(tmp_path)

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
    acesso_pin = AcessoPin(tmp_path / "acesso_pin.json")
    acesso_pin.configurar("benedito", "benedito", "123456")
    cliente = TestClient(
        criar_app(pasta_rostos=tmp_path, acesso_pin=acesso_pin, cadastros=cadastros)
    )

    primeira = cliente.post("/cadastro/ana/amostra", content=jpeg()).json()
    segunda = cliente.post("/cadastro/ana/amostra", content=jpeg()).json()

    assert primeira["estado"] == "capturada"
    assert segunda["estado"] == "concluido"
    cliente.post("/sessao/pin", json={"identificador": "benedito", "pin": "123456"})
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


def test_quadro_devolve_os_pontos_do_rosto(tmp_path):
    import numpy as np

    linha = np.array(
        [100, 10, 200, 240, 150, 80, 250, 80, 200, 140, 160, 200, 240, 200, 0.9], dtype=np.float32
    )
    rosto = Rosto(topo=10, direita=300, base=250, esquerda=100, deteccao=linha)
    cliente = cliente_com_roteiro(
        tmp_path, [Avaliacao(EstadoDesbloqueio.RECONHECENDO, 0.4, None, [rosto])]
    )

    pontos = cliente.post("/desbloqueio/quadro", content=jpeg()).json()["rostos"][0]["pontos"]

    assert [p["nome"] for p in pontos] == [
        "olho_direito",
        "olho_esquerdo",
        "nariz",
        "boca_direita",
        "boca_esquerda",
    ]
    assert (pontos[2]["x"], pontos[2]["y"]) == (200, 140)
