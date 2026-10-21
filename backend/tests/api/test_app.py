import json
from datetime import datetime

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.api.app import aviso_de_atrasados
from jarvis.api.cadastros import Cadastros
from jarvis.api.sessao import Sessao
from jarvis.habilidades import HABILIDADES
from jarvis.habilidades.conversa.cerebro import (
    Cartao,
    CerebroIndisponivelError,
    Fim,
    Frase,
    RespostaDaIA,
    Usando,
)
from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.conversa.memoria import Memoria
from jarvis.habilidades.conversa.transcricao import TranscricaoIndisponivelError
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.cadastro import Cadastro as CadastroDeVerdade
from jarvis.habilidades.desbloqueio_facial.cadastro import EstadoCadastro, ResultadoAmostra
from jarvis.habilidades.desbloqueio_facial.desbloqueio import Avaliacao, EstadoDesbloqueio
from jarvis.habilidades.desbloqueio_facial.reconhecedor import Rosto
from jarvis.habilidades.lembretes.agenda import Agenda, Lembrete
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

    def enfileirar(self, frase):
        self.frases.append(frase)

    def calar(self):
        pass


def ler_conversa(resposta):
    """Lê o fluxo NDJSON da conversa num dicionário só, para os testes."""
    eventos = [json.loads(linha) for linha in resposta.text.splitlines() if linha]
    ouvido = next(e for e in eventos if e["tipo"] == "ouvido")
    trechos = [e["texto"] for e in eventos if e["tipo"] == "trecho"]
    fim = eventos[-1]
    assert fim["tipo"] == "fim"  # o fluxo sempre termina com "fim"
    return {
        "texto": ouvido["texto"],
        "arquivo": ouvido["arquivo"],
        "resposta": " ".join(trechos) if trechos else None,
        "acao": fim["acao"],
        "eventos": [e["tipo"] for e in eventos],
    }


class CerebroFalso:
    def __init__(self, fala="Um omelete resolve.", erro=None, antes=()):
        self.fala = fala
        self.erro = erro
        self.antes = list(antes)  # eventos antes da fala (ferramentas, cartões)
        self.perguntas = []
        self.historicos = []
        self.ferramentas = []

    def responder_em_fluxo(self, pergunta, usuario, historico=(), ferramentas=()):
        self.perguntas.append((pergunta, usuario))
        self.historicos.append(list(historico))
        self.ferramentas = list(ferramentas)
        if self.erro:
            raise self.erro
        yield from self.antes
        yield Frase(self.fala)
        troca = [
            {"role": "user", "content": pergunta},
            {"role": "assistant", "content": self.fala},
        ]
        yield Fim(RespostaDaIA(fala=self.fala, troca=troca))


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
    corpo = ler_conversa(resposta)
    assert corpo["arquivo"].endswith(".webm")
    assert (tmp_path / corpo["arquivo"]).read_bytes() == b"isto seria um webm"


def test_gravacao_volta_com_o_que_foi_dito(tmp_path):
    transcritor = TranscritorFalso("que horas são")
    cliente = cliente_de_gravacao(tmp_path, transcritor)

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["texto"] == "que horas são"
    assert transcritor.ouvidos == [tmp_path / corpo["arquivo"]]


def test_pergunta_a_hora_e_o_jarvis_responde_em_voz(tmp_path):
    locutor = LocutorQueAnota()
    sessao = Sessao(tmp_path / "rostos", locutor=locutor)
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("Que horas são?"), sessao)

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["resposta"].startswith(("São", "É"))
    assert corpo["acao"] is None
    assert locutor.frases == [corpo["resposta"]]


def test_pedir_para_bloquear_bloqueia_a_sessao(tmp_path):
    sessao = Sessao(tmp_path / "rostos", locutor=LocutorQueAnota())
    sessao._usuario = "benedito"  # como se já tivesse desbloqueado
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("Jarvis, bloquear"), sessao)

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["acao"] == "bloquear"
    assert sessao.usuario is None


def test_pedido_desconhecido_responde_que_ainda_nao_sabe(tmp_path):
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("abre o Spotify"))

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["resposta"] == "Ainda não sei fazer isso."


def test_pergunta_livre_vai_para_o_cerebro_e_e_falada(tmp_path):
    locutor = LocutorQueAnota()
    cerebro = CerebroFalso("Um omelete resolve.")
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("ideia de jantar?"), sessao_aberta(tmp_path, locutor), cerebro
    )

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

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

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert cerebro.perguntas == []
    assert corpo["resposta"] == "Ainda não sei fazer isso."


def test_ia_fora_do_ar_avisa_em_voz(tmp_path):
    cerebro = CerebroFalso(erro=CerebroIndisponivelError("sem crédito"))
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("ideia de jantar?"), sessao_aberta(tmp_path), cerebro
    )

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["resposta"].startswith("Não consegui pensar nisso agora")


def test_a_ia_lembra_das_trocas_anteriores(tmp_path):
    cerebro = CerebroFalso("Amanhã é quarta.")
    transcritor = TranscritorFalso("que horas são")
    cliente = cliente_de_gravacao(tmp_path, transcritor, sessao_aberta(tmp_path), cerebro)
    cliente.post("/conversa/gravacao", content=b"voz")  # comando local, vai para a memória

    transcritor.texto = "e amanhã?"
    cliente.post("/conversa/gravacao", content=b"voz")

    [historico] = cerebro.historicos
    assert historico[0] == {"role": "user", "content": "que horas são"}
    assert historico[1]["role"] == "assistant"


def test_a_ia_recebe_todas_as_ferramentas(tmp_path):
    cerebro = CerebroFalso()
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("me lembra de algo"), sessao_aberta(tmp_path), cerebro
    )

    cliente.post("/conversa/gravacao", content=b"voz")

    assert [f.nome for f in cerebro.ferramentas] == [
        "criar_lembrete",
        "listar_lembretes",
        "pesquisar_web",
        "clima",
        "noticias",
        "abrir_site",
        "abrir_app",
        "anotar",
        "ler_notas",
        "calcular",
    ]


def test_bloquear_esquece_a_conversa(tmp_path):
    memoria = Memoria()
    memoria.lembrar("segredo", "ok")
    sessao = sessao_aberta(tmp_path)
    cliente = TestClient(criar_app(pasta_gravacoes=tmp_path, sessao=sessao, memoria=memoria))

    cliente.post("/sessao/bloquear")

    assert memoria.recentes() == []


def test_lembretes_pendentes_so_com_o_jarvis_aberto(tmp_path):
    agenda = Agenda(avisar=lambda _: None, agendar=lambda _s, _a: None)
    agenda.criar(20, "ligar pro dentista")
    sessao = sessao_aberta(tmp_path)
    cliente = TestClient(criar_app(pasta_gravacoes=tmp_path, sessao=sessao, agenda=agenda))

    [lembrete] = cliente.get("/lembretes").json()
    assert lembrete["texto"] == "ligar pro dentista"

    cliente.post("/sessao/bloquear")
    assert cliente.get("/lembretes").json() == []


def test_sem_fala_nao_responde_nada(tmp_path):
    locutor = LocutorQueAnota()
    sessao = Sessao(tmp_path / "rostos", locutor=locutor)
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso(""), sessao)

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

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


def test_aviso_de_lembretes_atrasados_numa_frase_so():
    um = Lembrete(1, "tirar o bolo", datetime(2026, 10, 20, 10, 20, tzinfo=FUSO))
    dois = Lembrete(2, "ligar pro João", datetime(2026, 10, 20, 11, 0, tzinfo=FUSO))

    assert aviso_de_atrasados([um]) == (
        "Enquanto eu estava desligado, venceu 1 lembrete: às 10 e 20, tirar o bolo."
    )
    assert "venceram 2 lembretes" in aviso_de_atrasados([um, dois])


def test_conversa_chega_em_fluxo_na_ordem_certa(tmp_path):
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("ideia de jantar?"), sessao_aberta(tmp_path), CerebroFalso()
    )

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["eventos"] == ["ouvido", "trecho", "fim"]


def test_cerebro_sem_resposta_diz_que_nao_sabe(tmp_path):
    class CerebroCalado(CerebroFalso):
        def responder_em_fluxo(self, *a, **k):
            yield Fim(RespostaDaIA(fala="", troca=[]))

    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("hm?"), sessao_aberta(tmp_path), CerebroCalado()
    )

    assert ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))["resposta"] == (
        "Ainda não sei fazer isso."
    )


# --- Conversa por texto (para quando não dá para falar) ---------------------------


def test_texto_digitado_segue_o_mesmo_fluxo_da_voz(tmp_path):
    cerebro = CerebroFalso("Um omelete resolve.")
    cliente = cliente_de_gravacao(tmp_path, sessao=sessao_aberta(tmp_path), cerebro=cerebro)

    corpo = ler_conversa(cliente.post("/conversa/texto", json={"texto": " ideia de jantar? "}))

    assert corpo["texto"] == "ideia de jantar?"
    assert corpo["arquivo"] is None  # não houve áudio
    assert corpo["resposta"] == "Um omelete resolve."
    assert cerebro.perguntas == [("ideia de jantar?", "Benedito")]


def test_texto_digitado_tambem_usa_os_comandos_locais(tmp_path):
    cliente = cliente_de_gravacao(tmp_path, sessao=sessao_aberta(tmp_path), cerebro=CerebroFalso())

    corpo = ler_conversa(cliente.post("/conversa/texto", json={"texto": "que horas são?"}))

    assert corpo["resposta"].startswith(("São", "É"))


@pytest.mark.parametrize("texto", ["", "x" * 501])
def test_texto_vazio_ou_grande_demais_e_recusado(tmp_path, texto):
    cliente = cliente_de_gravacao(tmp_path)

    assert cliente.post("/conversa/texto", json={"texto": texto}).status_code == 422


def test_ferramenta_e_cartao_chegam_no_fluxo_antes_da_fala(tmp_path):
    cartao = {"tipo": "clima", "rotulo": "Clima", "titulo": "Fortaleza", "temperatura": 30}
    cerebro = CerebroFalso("Faz 30 graus.", antes=[Usando("clima"), Cartao(cartao)])
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("e o clima?"), sessao_aberta(tmp_path), cerebro
    )

    resposta = cliente.post("/conversa/gravacao", content=b"voz")

    eventos = [json.loads(linha) for linha in resposta.text.splitlines() if linha]
    assert [e["tipo"] for e in eventos] == ["ouvido", "usando", "cartao", "trecho", "fim"]
    assert eventos[1]["ferramenta"] == "clima"
    assert eventos[2]["cartao"] == cartao


FEED_FALSO = (
    b"<rss><channel><item><title>Dolar cai - G1</title><source>G1</source></item></channel></rss>"
)


def clima_falso(url):
    if "geocoding" in url:
        return {"results": [{"name": "Fortaleza", "latitude": 0, "longitude": 0}]}
    return {
        "current": {
            "temperature_2m": 27,
            "apparent_temperature": 30,
            "weather_code": 0,
            "relative_humidity_2m": 70,
        },
        "daily": {
            "time": ["2026-10-21"],
            "weather_code": [0],
            "temperature_2m_max": [31],
            "temperature_2m_min": [24],
            "precipitation_probability_max": [0],
        },
    }


def cliente_de_bom_dia(tmp_path, sessao, cerebro=None):
    return TestClient(
        criar_app(
            pasta_gravacoes=tmp_path,
            transcritor=TranscritorFalso("Jarvis, bom dia"),
            sessao=sessao,
            cerebro=cerebro,
            obter_clima=clima_falso,
            obter_noticias=lambda url: FEED_FALSO,
        )
    )


def test_bom_dia_conta_o_dia_com_um_cartao_antes_de_cada_assunto(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")
    locutor = LocutorQueAnota()
    cerebro = CerebroFalso()
    cliente = cliente_de_bom_dia(tmp_path, sessao_aberta(tmp_path, locutor), cerebro)

    resposta = cliente.post("/conversa/gravacao", content=b"voz")

    eventos = [json.loads(linha) for linha in resposta.text.splitlines() if linha]
    assert [e["tipo"] for e in eventos] == [
        "ouvido",
        "trecho",  # o cumprimento sai na hora, enquanto busca o resto
        "usando",
        "usando",
        "usando",
        "cartao",
        "trecho",
        "cartao",
        "trecho",
        "cartao",
        "trecho",
        "fim",
    ]  # uma notícia só no feed falso: um cartão para ela
    assert [e["ferramenta"] for e in eventos if e["tipo"] == "usando"] == [
        "clima",
        "listar_lembretes",
        "noticias",
    ]
    assert [e["cartao"]["tipo"] for e in eventos if e["tipo"] == "cartao"] == [
        "clima",
        "lembretes",
        "noticia",
    ]
    assert locutor.frases[0].startswith(("Bom dia", "Boa tarde", "Boa noite"))
    assert locutor.frases[1].startswith("Em Fortaleza, agora faz 27 graus")
    assert locutor.frases[2] == "Nenhum lembrete para hoje."
    assert "Dolar cai" in locutor.frases[3]
    assert cerebro.perguntas == []  # sem IA: sai rápido e de graça


def test_depois_do_bom_dia_a_ia_lembra_das_noticias(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")
    transcritor = TranscritorFalso("bom dia")
    cerebro = CerebroFalso()
    cliente = TestClient(
        criar_app(
            pasta_gravacoes=tmp_path,
            transcritor=transcritor,
            sessao=sessao_aberta(tmp_path),
            cerebro=cerebro,
            obter_clima=clima_falso,
            obter_noticias=lambda url: FEED_FALSO,
        )
    )
    cliente.post("/conversa/gravacao", content=b"voz")

    transcritor.texto = "detalha a primeira"
    cliente.post("/conversa/gravacao", content=b"voz")

    [historico] = cerebro.historicos
    assert "Dolar cai" in historico[1]["content"]


def test_bom_dia_bloqueado_e_so_um_cumprimento(tmp_path):
    locutor = LocutorQueAnota()
    cliente = cliente_de_bom_dia(tmp_path, Sessao(tmp_path / "rostos", locutor=locutor))

    corpo = ler_conversa(cliente.post("/conversa/gravacao", content=b"voz"))

    assert corpo["resposta"] == "Bom dia."
    assert "cartao" not in corpo["eventos"]


# --- Escuta sem tecla ---------------------------------------------------------------

ORIGEM_DO_APP = {"origin": "http://localhost:1420"}


class DetectorFalso:
    """Ouve "Jarvis" quando o som traz a amostra 7 (o resto é silêncio)."""

    def __init__(self):
        self.recebido = 0

    def ouvir(self, pcm):
        self.recebido += len(pcm)
        return bool((pcm == 7).any())


def cliente_de_escuta(tmp_path, sessao, criar_detector=DetectorFalso):
    return TestClient(
        criar_app(pasta_gravacoes=tmp_path, sessao=sessao, criar_detector=criar_detector)
    )


def test_escuta_avisa_quando_ouve_jarvis(tmp_path):
    cliente = cliente_de_escuta(tmp_path, sessao_aberta(tmp_path))

    with cliente.websocket_connect("/escuta", headers=ORIGEM_DO_APP) as canal:
        assert canal.receive_json() == {"tipo": "pronta"}
        canal.send_bytes(np.zeros(1280, "<i2").tobytes())
        canal.send_bytes(np.full(1280, 7, "<i2").tobytes())

        assert canal.receive_json() == {"tipo": "jarvis"}


def test_escuta_recusa_outra_origem(tmp_path):
    from starlette.websockets import WebSocketDisconnect

    cliente = cliente_de_escuta(tmp_path, sessao_aberta(tmp_path))

    with pytest.raises(WebSocketDisconnect) as erro:
        with cliente.websocket_connect("/escuta", headers={"origin": "https://site-malicioso.com"}):
            pass
    assert erro.value.code == 1008


def test_escuta_bloqueada_nao_ouve(tmp_path):
    from starlette.websockets import WebSocketDisconnect

    cliente = cliente_de_escuta(tmp_path, Sessao(tmp_path / "rostos", locutor=LocutorQueAnota()))

    with pytest.raises(WebSocketDisconnect):
        with cliente.websocket_connect("/escuta", headers=ORIGEM_DO_APP):
            pass


def test_escuta_sem_treino_avisa_que_esta_indisponivel(tmp_path):
    from jarvis.habilidades.escuta.detector import EscutaIndisponivelError

    def sem_treino():
        raise EscutaIndisponivelError("A escuta ainda não foi treinada com a sua voz.")

    cliente = cliente_de_escuta(tmp_path, sessao_aberta(tmp_path), sem_treino)

    with cliente.websocket_connect("/escuta", headers=ORIGEM_DO_APP) as canal:
        resposta = canal.receive_json()
    assert resposta["tipo"] == "indisponivel"
    assert "treinada" in resposta["motivo"]


def test_chamado_pela_voz_sem_o_nome_e_descartado_e_apagado(tmp_path):
    cerebro = CerebroFalso()
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("e aí, vamos ver o jogo"), sessao_aberta(tmp_path), cerebro
    )

    resposta = cliente.post("/conversa/gravacao?chamado=true", content=b"voz")

    eventos = [json.loads(linha) for linha in resposta.text.splitlines() if linha]
    assert eventos == [{"tipo": "ignorado"}]
    assert not list(tmp_path.glob("*.webm"))  # não guarda conversa alheia
    assert cerebro.perguntas == []


def test_chamado_pela_voz_com_o_nome_segue_a_conversa(tmp_path):
    cliente = cliente_de_gravacao(
        tmp_path, TranscritorFalso("Jarvis, que horas são?"), sessao_aberta(tmp_path)
    )

    corpo = ler_conversa(cliente.post("/conversa/gravacao?chamado=true", content=b"voz"))

    assert corpo["resposta"].startswith(("São", "É"))
    assert list(tmp_path.glob("*.webm"))


def test_so_o_nome_responde_pois_nao_e_pede_para_escutar(tmp_path):
    cliente = cliente_de_gravacao(tmp_path, TranscritorFalso("Jarvis?"), sessao_aberta(tmp_path))

    corpo = ler_conversa(cliente.post("/conversa/gravacao?chamado=true", content=b"voz"))

    assert corpo["resposta"] == "Pois não?"
    assert corpo["acao"] == "escutar"
