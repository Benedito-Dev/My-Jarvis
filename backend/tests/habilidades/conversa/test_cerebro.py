from datetime import datetime

import pytest

from jarvis.habilidades.conversa.cerebro import (
    Cerebro,
    CerebroIndisponivelError,
    criar_cerebro,
    limpar_para_falar,
)
from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.conversa.ferramentas import Ferramenta, Resultado

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

    assert cerebro.responder("ideia de jantar?", "Benedito", AGORA).fala == (
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


# --- Memória e ferramentas ------------------------------------------------------


class OpenRouterRoteirizado:
    """Responde, em ordem, as mensagens do roteiro (uma por pedido)."""

    def __init__(self, *mensagens):
        self.roteiro = list(mensagens)
        self.pedidos = []

    def enviar(self, corpo, _chave):
        self.pedidos.append(corpo)
        return {"choices": [{"message": self.roteiro.pop(0)}]}


def chamada_de(nome, argumentos):
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": [
            {"id": "c1", "type": "function", "function": {"name": nome, "arguments": argumentos}}
        ],
    }


def ferramenta_de_teste(fala):
    usadas = []

    def executar(parametros):
        usadas.append(parametros)
        return Resultado(para_ia="feito", fala=fala)

    return Ferramenta("acao", "faz algo", {"type": "object"}, executar), usadas


def test_manda_o_historico_antes_da_pergunta():
    falso = OpenRouterRoteirizado({"content": "Amanhã é quarta."})
    historico = [
        {"role": "user", "content": "que dia é hoje?"},
        {"role": "assistant", "content": "Hoje é terça."},
    ]

    Cerebro("k", enviar=falso.enviar).responder("e amanhã?", "Benedito", AGORA, historico)

    mensagens = falso.pedidos[0]["messages"]
    assert mensagens[1:] == [*historico, {"role": "user", "content": "e amanhã?"}]


def test_ferramenta_com_fala_pronta_responde_sem_voltar_a_ia():
    ferramenta, usadas = ferramenta_de_teste(fala="Certo. Te aviso às 10 e 25.")
    falso = OpenRouterRoteirizado(chamada_de("acao", '{"x": 1}'))

    resposta = Cerebro("k", enviar=falso.enviar).responder(
        "me lembra", "Benedito", AGORA, ferramentas=[ferramenta]
    )

    assert resposta.fala == "Certo. Te aviso às 10 e 25."
    assert usadas == [{"x": 1}]
    assert len(falso.pedidos) == 1  # uma viagem só
    assert falso.pedidos[0]["tools"][0]["function"]["name"] == "acao"


def test_ferramenta_sem_fala_volta_a_ia_com_o_resultado():
    ferramenta, _ = ferramenta_de_teste(fala=None)
    falso = OpenRouterRoteirizado(chamada_de("acao", "{}"), {"content": "Pronto, feito."})

    resposta = Cerebro("k", enviar=falso.enviar).responder(
        "faz", "Benedito", AGORA, ferramentas=[ferramenta]
    )

    assert resposta.fala == "Pronto, feito."
    resultado = falso.pedidos[1]["messages"][-1]
    assert resultado == {"role": "tool", "tool_call_id": "c1", "content": "feito"}


def test_ia_presa_usando_ferramentas_desiste():
    ferramenta, _ = ferramenta_de_teste(fala=None)
    falso = OpenRouterRoteirizado(*[chamada_de("acao", "{}")] * 5)

    with pytest.raises(CerebroIndisponivelError):
        Cerebro("k", enviar=falso.enviar).responder("faz", "B", AGORA, ferramentas=[ferramenta])


def test_a_troca_guarda_a_ferramenta_usada_para_a_memoria():
    # Sem isto, a memória só teria "Certo..." e a IA aprenderia a fingir a ação.
    ferramenta, _ = ferramenta_de_teste(fala="Certo.")
    falso = OpenRouterRoteirizado(chamada_de("acao", "{}"))

    troca = (
        Cerebro("k", enviar=falso.enviar)
        .responder("faz", "B", AGORA, ferramentas=[ferramenta])
        .troca
    )

    assert [m["role"] for m in troca] == ["user", "assistant", "tool", "assistant"]
    assert troca[1]["tool_calls"][0]["function"]["name"] == "acao"
    assert troca[-1] == {"role": "assistant", "content": "Certo."}


def test_troca_sem_ferramenta_e_pergunta_e_resposta():
    falso = OpenRouterRoteirizado({"content": "Quatro."})

    troca = Cerebro("k", enviar=falso.enviar).responder("2+2?", "B", AGORA).troca

    assert troca == [
        {"role": "user", "content": "2+2?"},
        {"role": "assistant", "content": "Quatro."},
    ]
