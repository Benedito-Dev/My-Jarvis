import subprocess
from datetime import datetime

from jarvis.habilidades.conversa import ferramentas
from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.lembretes.agenda import Agenda
from jarvis.habilidades.notas.caderno import Caderno
from jarvis.habilidades.pesquisa.web import PesquisaIndisponivelError

AGORA = datetime(2026, 10, 20, 10, 5, tzinfo=FUSO)


def agenda_parada():
    return Agenda(avisar=lambda _: None, agendar=lambda _s, _a: None, relogio=lambda: AGORA)


def test_lembrete_agenda_e_confirma_com_o_horario():
    agenda = agenda_parada()
    ferramenta = ferramentas.lembrete(agenda)

    resultado = ferramenta.executar({"daqui_a_minutos": 20, "texto": "ligar pro dentista"})

    assert resultado.fala == "Certo. Te aviso às 10 e 25."
    assert [lem.texto for lem in agenda.pendentes()] == ["ligar pro dentista"]


def test_lembrete_invalido_e_contado_a_ia_sem_fala_pronta():
    resultado = ferramentas.lembrete(agenda_parada()).executar(
        {"daqui_a_minutos": 99999, "texto": "x"}
    )

    assert resultado.fala is None
    assert "Não agendado" in resultado.para_ia


def test_formato_da_ia():
    [descricao] = ferramentas.no_formato_da_ia([ferramentas.lembrete(agenda_parada())])

    assert descricao["type"] == "function"
    assert descricao["function"]["name"] == "criar_lembrete"
    assert "daqui_a_minutos" in descricao["function"]["parameters"]["properties"]


def test_executar_ferramenta_que_nao_existe_nao_quebra():
    resultado = ferramentas.executar([], "voar", "{}")

    assert "não existe" in resultado.para_ia


def test_executar_com_json_quebrado_nao_quebra():
    lista = [ferramentas.lembrete(agenda_parada())]

    assert "JSON" in ferramentas.executar(lista, "criar_lembrete", "{quebrado").para_ia


def test_listar_lembretes_conta_a_ia_o_que_esta_pendente():
    agenda = agenda_parada()
    agenda.criar(20, "ligar pro dentista")

    resultado = ferramentas.listar_lembretes(agenda).executar({})

    assert resultado.para_ia == "Lembretes pendentes: às 10 e 25: ligar pro dentista."
    assert resultado.fala is None  # a IA monta a frase


def test_listar_sem_lembretes():
    assert "Nenhum" in ferramentas.listar_lembretes(agenda_parada()).executar({}).para_ia


# --- O lote 2: web, clima, abrir, notas, calculadora ----------------------------


def test_pesquisar_web_entrega_os_achados_a_ia():
    def busca(consulta, noticias):
        return [{"title": "Flamengo empata", "body": "1 a 1", "href": "ge"}]

    resultado = ferramentas.pesquisar_web(buscar=busca).executar({"consulta": "flamengo"})

    assert "Flamengo empata: 1 a 1" in resultado.para_ia
    assert resultado.fala is None  # a IA resume


def test_pesquisa_que_falha_vira_aviso_para_a_ia():
    def busca(consulta, noticias):
        raise PesquisaIndisponivelError("Ratelimit")

    resultado = ferramentas.pesquisar_web(buscar=busca).executar({"consulta": "x"})

    assert "falhou" in resultado.para_ia


def test_clima_sem_cidade_pede_para_perguntar(monkeypatch):
    monkeypatch.delenv("JARVIS_CIDADE", raising=False)

    resultado = ferramentas.clima(obter=lambda url: {}).executar({})

    assert "Pergunte" in resultado.para_ia


def test_clima_usa_a_cidade_padrao(monkeypatch):
    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")
    pedidas = []

    def obter(url):
        pedidas.append(url)
        return {"results": []}  # cidade "não encontrada": só queremos ver o pedido

    ferramentas.clima(obter=obter).executar({})

    assert "name=Fortaleza" in pedidas[0]


def test_abrir_app_confirma_em_voz():
    rodados = []

    def rodar(comando, **_):
        rodados.append(comando)
        return subprocess.CompletedProcess(comando, 0)

    resultado = ferramentas.abrir_app(rodar=rodar).executar({"nome": "Spotify"})

    assert resultado.fala == "Abrindo o Spotify."
    assert rodados and "Spotify" in rodados[0][-1]


def test_abrir_site_invalido_avisa_a_ia_sem_abrir():
    resultado = ferramentas.abrir_site(rodar=lambda *a, **k: None).executar(
        {"endereco": "file:///etc/passwd"}
    )

    assert resultado.fala is None
    assert "inválido" in resultado.para_ia


def test_anotar_e_ler(tmp_path):
    caderno = Caderno(tmp_path / "notas.json")

    assert ferramentas.anotar(caderno).executar({"texto": "comprar café"}).fala == "Anotado."
    assert "comprar café" in ferramentas.ler_notas(caderno).executar({}).para_ia


def test_calcular_entrega_o_resultado_exato():
    resultado = ferramentas.calcular().executar({"expressao": "3480 * 17 / 100"})

    assert resultado.para_ia == "3480 * 17 / 100 = 591.6"


# --- Cartões: o que a tela mostra junto com a fala ---------------------------------


def test_lembrete_criado_vira_cartao_com_a_hora():
    resultado = ferramentas.lembrete(agenda_parada()).executar(
        {"daqui_a_minutos": 20, "texto": "ligar pro dentista"}
    )

    assert resultado.cartao == {
        "tipo": "lembretes",
        "rotulo": "Lembrete criado",
        "titulo": "1 lembrete",
        "itens": [{"hora": "10:25", "texto": "ligar pro dentista"}],
    }


def test_lembrete_invalido_nao_tem_cartao():
    resultado = ferramentas.lembrete(agenda_parada()).executar(
        {"daqui_a_minutos": 99999, "texto": "x"}
    )

    assert resultado.cartao is None


def test_pesquisa_vira_cartao_com_ate_tres_achados():
    def busca(consulta, noticias):
        return [{"title": f"T{i}", "body": "b", "href": "f"} for i in range(5)]

    cartao = (
        ferramentas.pesquisar_web(buscar=busca)
        .executar({"consulta": "iphone", "noticias": True})
        .cartao
    )

    assert (cartao["tipo"], cartao["rotulo"], cartao["titulo"]) == (
        "pesquisa",
        "Notícias",
        "iphone",
    )
    assert [item["titulo"] for item in cartao["itens"]] == ["T0", "T1", "T2"]


def test_pesquisa_sem_achados_nao_tem_cartao():
    resultado = ferramentas.pesquisar_web(buscar=lambda c, n: []).executar({"consulta": "x"})

    assert resultado.cartao is None


def test_clima_vira_cartao(monkeypatch):
    monkeypatch.setenv("JARVIS_CIDADE", "Fortaleza")
    lugar = {"results": [{"name": "Fortaleza", "latitude": 0, "longitude": 0}]}
    previsao = {
        "current": {
            "temperature_2m": 30,
            "apparent_temperature": 33,
            "weather_code": 0,
            "relative_humidity_2m": 60,
        },
        "daily": {
            "time": ["2026-10-20"],
            "weather_code": [0],
            "temperature_2m_max": [32],
            "temperature_2m_min": [25],
            "precipitation_probability_max": [10],
        },
    }

    resultado = ferramentas.clima(
        obter=lambda url: lugar if "geocoding" in url else previsao
    ).executar({})

    assert resultado.cartao["tipo"] == "clima"
    assert resultado.cartao["temperatura"] == 30


def test_notas_e_conta_viram_cartao(tmp_path):
    caderno = Caderno(tmp_path / "notas.json")

    anotado = ferramentas.anotar(caderno).executar({"texto": "comprar café"}).cartao
    lidas = ferramentas.ler_notas(caderno).executar({}).cartao
    conta = ferramentas.calcular().executar({"expressao": "3480 * 17 / 100"}).cartao

    assert anotado["itens"] == ["comprar café"]
    assert (lidas["titulo"], lidas["itens"]) == ("1 anotação", ["comprar café"])
    assert (conta["titulo"], conta["expressao"]) == ("591,6", "3480 * 17 / 100")


def test_noticias_traz_manchetes_e_cartao():
    feed = (
        b"<rss><channel><item><title>Dolar cai - G1</title>"
        b"<source>G1</source></item></channel></rss>"
    )

    resultado = ferramentas.noticias(obter=lambda url: feed).executar({})

    assert resultado.para_ia == "Manchetes de agora:\n- Dolar cai (G1)"
    assert resultado.cartao["rotulo"] == "Notícias"
