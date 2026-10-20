from datetime import datetime

import pytest

from jarvis.habilidades.conversa.cerebro import (
    Cartao,
    Cerebro,
    CerebroIndisponivelError,
    Fim,
    Frase,
    Usando,
    criar_cerebro,
    limpar_para_falar,
)
from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.habilidades.conversa.ferramentas import Ferramenta, Resultado

AGORA = datetime(2026, 10, 20, 9, 30, tzinfo=FUSO)


def em_pedacos(resposta):
    """Simula o fluxo (stream) do OpenRouter: o texto chega picado, de 6 em 6
    letras, e cada chamada de ferramenta chega com o nome numa parte e os
    argumentos em outras. Erros chegam como estão."""
    if "error" in resposta:
        yield resposta
        return
    mensagem = resposta["choices"][0]["message"]
    texto = mensagem.get("content") or ""
    for i in range(0, len(texto), 6):
        yield {"choices": [{"delta": {"content": texto[i : i + 6]}}]}
    for indice, chamada in enumerate(mensagem.get("tool_calls") or []):
        nome = chamada["function"]["name"]
        argumentos = chamada["function"]["arguments"]
        inicio = {"index": indice, "id": chamada["id"], "function": {"name": nome}}
        yield {"choices": [{"delta": {"tool_calls": [inicio]}}]}
        for j in range(0, len(argumentos), 4):
            parte = {"index": indice, "function": {"arguments": argumentos[j : j + 4]}}
            yield {"choices": [{"delta": {"tool_calls": [parte]}}]}


class OpenRouterFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.pedidos = []

    def enviar(self, corpo, chave):
        self.pedidos.append((corpo, chave))
        return em_pedacos(self.resposta)


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
        return em_pedacos({"choices": [{"message": self.roteiro.pop(0)}]})


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


# --- Em fluxo: o Jarvis começa a falar antes da IA terminar ----------------------


def test_cada_frase_sai_assim_que_fecha():
    texto = "Claro, senhor, um omelete resolve o jantar. Fica pronto em cinco minutos, no máximo."
    falso = OpenRouterFalso(resposta_com(texto))

    eventos = list(Cerebro("k", enviar=falso.enviar).responder_em_fluxo("jantar?", "B", AGORA))

    frases = [e.texto for e in eventos if isinstance(e, Frase)]
    assert frases == [
        "Claro, senhor, um omelete resolve o jantar.",
        "Fica pronto em cinco minutos, no máximo.",
    ]
    assert isinstance(eventos[-1], Fim)
    assert eventos[-1].resposta.fala == texto


def test_ferramenta_picada_no_fluxo_e_montada_inteira():
    ferramenta, usadas = ferramenta_de_teste(fala="Certo.")
    falso = OpenRouterRoteirizado(chamada_de("acao", '{"daqui_a_minutos": 20, "texto": "x"}'))

    list(
        Cerebro("k", enviar=falso.enviar).responder_em_fluxo(
            "me lembra", "B", AGORA, ferramentas=[ferramenta]
        )
    )

    assert usadas == [{"daqui_a_minutos": 20, "texto": "x"}]


def test_pede_a_resposta_sem_raciocinio():
    falso = OpenRouterFalso(resposta_com("ok"))

    Cerebro("k", enviar=falso.enviar).responder("oi", "B", AGORA)

    assert falso.pedidos[0][0]["reasoning"] == {"enabled": False}


def test_ferramenta_avisa_que_esta_em_uso_e_entrega_o_cartao():
    cartao = {"tipo": "clima", "rotulo": "Clima", "titulo": "Fortaleza"}
    ferramenta = Ferramenta(
        "clima", "o tempo", {"type": "object"}, lambda _p: Resultado("30 graus", cartao=cartao)
    )
    falso = OpenRouterRoteirizado(chamada_de("clima", "{}"), {"content": "Faz 30 graus."})

    eventos = list(
        Cerebro("k", enviar=falso.enviar).responder_em_fluxo(
            "e o clima?", "Benedito", AGORA, ferramentas=[ferramenta]
        )
    )

    # Primeiro avisa, depois mostra, e só então a IA fala sobre o resultado.
    assert eventos[:3] == [Usando("clima"), Cartao(cartao), Frase("Faz 30 graus.")]
    assert isinstance(eventos[-1], Fim)
