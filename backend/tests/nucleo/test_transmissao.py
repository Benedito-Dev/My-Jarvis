import queue

from jarvis.nucleo.transmissao import MAXIMO_NA_FILA, Transmissao


def test_todo_assinante_recebe():
    transmissao = Transmissao()
    a, b = transmissao.assinar(), transmissao.assinar()

    transmissao.publicar({"tipo": "fala"})

    assert a.get_nowait() == b.get_nowait() == {"tipo": "fala"}


def test_quem_cancelou_nao_recebe_mais():
    transmissao = Transmissao()
    fila = transmissao.assinar()
    transmissao.cancelar(fila)

    transmissao.publicar({"tipo": "fala"})

    assert fila.empty()


def test_assinante_lento_nao_trava_quem_publica():
    transmissao = Transmissao()
    fila = transmissao.assinar()

    for i in range(MAXIMO_NA_FILA + 10):
        transmissao.publicar({"i": i})  # não pode travar nem levantar erro

    assert fila.qsize() == MAXIMO_NA_FILA
    assert isinstance(fila, queue.Queue)
