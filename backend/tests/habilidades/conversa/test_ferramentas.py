from datetime import datetime

from jarvis.habilidades.conversa import ferramentas
from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.lembretes.agenda import Agenda

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
