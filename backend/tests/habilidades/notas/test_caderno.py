from datetime import datetime

import pytest

from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.notas.caderno import Caderno, NotaInvalidaError

AGORA = datetime(2026, 10, 20, 10, 30, tzinfo=FUSO)


def test_anota_e_lista_em_ordem(tmp_path):
    caderno = Caderno(tmp_path / "notas.json", relogio=lambda: AGORA)

    caderno.anotar("comprar café")
    caderno.anotar(" ligar pro João ")

    notas = caderno.listar()
    assert [n.texto for n in notas] == ["comprar café", "ligar pro João"]
    assert [n.id for n in notas] == [1, 2]
    assert notas[0].criada == "2026-10-20T10:30:00-03:00"


def test_notas_sobrevivem_a_reiniciar(tmp_path):
    Caderno(tmp_path / "notas.json").anotar("comprar café")

    assert [n.texto for n in Caderno(tmp_path / "notas.json").listar()] == ["comprar café"]


def test_sem_arquivo_nao_ha_notas(tmp_path):
    assert Caderno(tmp_path / "nao-existe.json").listar() == []


@pytest.mark.parametrize("texto", ["", "   ", "x" * 501])
def test_recusa_nota_invalida(tmp_path, texto):
    with pytest.raises(NotaInvalidaError):
        Caderno(tmp_path / "notas.json").anotar(texto)
