from datetime import datetime

import pytest

from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.lembretes.agenda import Agenda, LembreteInvalidoError

AGORA = datetime(2026, 10, 20, 10, 5, tzinfo=FUSO)


class AgendadorFalso:
    """Guarda as ações em vez de esperar: o teste dispara quando quiser."""

    def __init__(self):
        self.agendados = []

    def agendar(self, segundos, acao):
        self.agendados.append((segundos, acao))
        return self

    def cancel(self):
        pass


def criar_agenda():
    avisados = []
    agendador = AgendadorFalso()
    agenda = Agenda(avisar=avisados.append, agendar=agendador.agendar, relogio=lambda: AGORA)
    return agenda, agendador, avisados


def test_agenda_para_daqui_a_x_minutos():
    agenda, agendador, _ = criar_agenda()

    lembrete = agenda.criar(20, "ligar pro dentista")

    assert lembrete.quando == datetime(2026, 10, 20, 10, 25, tzinfo=FUSO)
    assert agendador.agendados[0][0] == 20 * 60


def test_na_hora_avisa_e_sai_dos_pendentes():
    agenda, agendador, avisados = criar_agenda()
    lembrete = agenda.criar(5, "tirar o bolo")
    assert agenda.pendentes() == [lembrete]

    agendador.agendados[0][1]()  # chegou a hora

    assert avisados == [lembrete]
    assert agenda.pendentes() == []


def test_pendentes_em_ordem_de_hora():
    agenda, _, _ = criar_agenda()
    depois = agenda.criar(30, "depois")
    antes = agenda.criar(5, "antes")

    assert agenda.pendentes() == [antes, depois]


@pytest.mark.parametrize(("minutos", "texto"), [(0, "x"), (-3, "x"), (2000, "x"), (5, "  ")])
def test_recusa_lembrete_invalido(minutos, texto):
    agenda, _, _ = criar_agenda()

    with pytest.raises(LembreteInvalidoError):
        agenda.criar(minutos, texto)


# --- Sobreviver a reinícios ---------------------------------------------------------


def agenda_com_arquivo(arquivo, relogio, agendador, avisados=None):
    return Agenda(
        avisar=(avisados if avisados is not None else []).append,
        agendar=agendador.agendar,
        relogio=relogio,
        arquivo=arquivo,
    )


def test_lembrete_volta_depois_de_reiniciar(tmp_path):
    arquivo = tmp_path / "lembretes.json"
    agenda_com_arquivo(arquivo, lambda: AGORA, AgendadorFalso()).criar(20, "ligar pro dentista")

    # "Reiniciou" 5 minutos depois: sobra 15 para tocar.
    depois = datetime(2026, 10, 20, 10, 10, tzinfo=FUSO)
    agendador = AgendadorFalso()
    nova = agenda_com_arquivo(arquivo, lambda: depois, agendador)
    atrasados = nova.restaurar(avisar_atrasado=lambda _: None)

    assert atrasados == []
    assert [lem.texto for lem in nova.pendentes()] == ["ligar pro dentista"]
    assert agendador.agendados[0][0] == 15 * 60


def test_lembrete_que_venceu_com_o_jarvis_desligado_e_avisado_ao_ligar(tmp_path):
    arquivo = tmp_path / "lembretes.json"
    agenda_com_arquivo(arquivo, lambda: AGORA, AgendadorFalso()).criar(5, "tirar o bolo")

    depois = datetime(2026, 10, 20, 11, 0, tzinfo=FUSO)
    nova = agenda_com_arquivo(arquivo, lambda: depois, AgendadorFalso())
    avisados_atrasados = []
    nova.restaurar(avisar_atrasado=avisados_atrasados.append)

    assert [lem.texto for lem in avisados_atrasados] == ["tirar o bolo"]
    assert nova.pendentes() == []
    assert '"tirar o bolo"' not in arquivo.read_text()  # não toca de novo no próximo reinício


def test_lembrete_que_tocou_sai_do_arquivo(tmp_path):
    arquivo = tmp_path / "lembretes.json"
    agendador = AgendadorFalso()
    agenda_com_arquivo(arquivo, lambda: AGORA, agendador).criar(5, "tirar o bolo")

    agendador.agendados[0][1]()  # tocou

    assert arquivo.read_text().strip() == "[]"


def test_ids_continuam_depois_de_reiniciar(tmp_path):
    arquivo = tmp_path / "lembretes.json"
    agenda_com_arquivo(arquivo, lambda: AGORA, AgendadorFalso()).criar(20, "um")

    nova = agenda_com_arquivo(arquivo, lambda: AGORA, AgendadorFalso())
    nova.restaurar(avisar_atrasado=lambda _: None)

    assert nova.criar(30, "dois").id == 2


def test_sem_arquivo_restaurar_nao_faz_nada():
    agenda, _, _ = criar_agenda()

    assert agenda.restaurar(avisar_atrasado=lambda _: None) == []
