from datetime import datetime

import pytest

from jarvis.habilidades.conversa.cerebro import (
    Cerebro,
    CerebroIndisponivelError,
    criar_cerebro,
    limpar_para_falar,
)
from jarvis.habilidades.conversa.comandos import FUSO

AGORA = datetime(2026, 10, 20, 9, 30, tzinfo=FUSO)


class OpenRouterFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.pedidos = []

    def enviar(self, corpo, chave):
        self.pedidos.append((corpo, chave))
        return self.resposta


def resposta_com(texto):
    return {"choices": [{"message": {"content": texto}}]}


def test_responde_com_o_texto_da_ia():
    falso = OpenRouterFalso(resposta_com("Um omelete resolve, Benedito."))
    cerebro = Cerebro("chave-x", enviar=falso.enviar)

    assert cerebro.responder("ideia de jantar?", "Benedito", AGORA) == (
        "Um omelete resolve, Benedito."
    )


def test_manda_a_personalidade_a_pergunta_e_a_chave():
    falso = OpenRouterFalso(resposta_com("ok"))
    Cerebro("chave-x", modelo="modelo-y", enviar=falso.enviar).responder("oi", "Benedito", AGORA)

    corpo, chave = falso.pedidos[0]
    sistema, usuario = corpo["messages"]
    assert chave == "chave-x"
    assert corpo["model"] == "modelo-y"
    assert "J.A.R.V.I.S." in sistema["content"] and "Benedito" in sistema["content"]
    assert "terça-feira, 20 de outubro" in sistema["content"]  # sabe o dia de hoje
    assert usuario == {"role": "user", "content": "oi"}


def test_tira_markdown_antes_de_falar():
    assert limpar_para_falar("**Claro!** Use `x` e\n\n# pronto") == "Claro! Use x e pronto"


def test_erro_da_ia_vira_cerebro_indisponivel():
    falso = OpenRouterFalso({"error": {"message": "Insufficient credits"}})

    with pytest.raises(CerebroIndisponivelError, match="Insufficient credits"):
        Cerebro("chave-x", enviar=falso.enviar).responder("oi", "Benedito", AGORA)


def test_sem_chave_nao_ha_cerebro(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    assert criar_cerebro() is None


def test_com_chave_ha_cerebro(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "chave-x")

    assert isinstance(criar_cerebro(), Cerebro)
