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
