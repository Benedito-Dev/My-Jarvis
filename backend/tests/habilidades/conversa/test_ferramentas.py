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
