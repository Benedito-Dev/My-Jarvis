"""Cérebro: responde perguntas livres com um modelo de IA, pelo OpenRouter.

Entra só quando os comandos fixos (`comandos.py`) não sabem o que fazer. Sai
da máquina apenas o TEXTO da pergunta: a voz e o rosto continuam locais.
A chave fica em `backend/.env` (fora do git), como OPENROUTER_API_KEY.
"""

import json
import os
import re
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime

from jarvis.habilidades.conversa import ferramentas as mod_ferramentas
from jarvis.habilidades.conversa.comandos import FUSO, falar_data, falar_hora
from jarvis.habilidades.conversa.ferramentas import Ferramenta

URL = "https://openrouter.ai/api/v1/chat/completions"
# O DeepSeek mais barato do OpenRouter em out/2026 (~US$ 0,00003 por pergunta).
MODELO = os.environ.get("JARVIS_MODELO_IA", "deepseek/deepseek-v4.1-flash")
TEMPO_LIMITE_S = 30
MAXIMO_DE_PALAVRAS = 300  # tokens de resposta: o Jarvis fala, não escreve redação
# Quantas vezes a IA pode usar ferramentas antes de responder. Evita um laço sem fim.
MAXIMO_DE_RODADAS = 3

PERSONALIDADE = """\
Você é o J.A.R.V.I.S., o assistente pessoal de {usuario}. \
Sua resposta vai ser FALADA em voz alta por um sintetizador, então:
- responda em português do Brasil, em no máximo 3 frases curtas;
- nada de listas, markdown, emojis ou links;
- escreva números como se fala ("384 mil quilômetros", não "384.400 km").
A pergunta vem de reconhecimento de voz e pode ter palavras trocadas \
("que iogas é o jogo" é "que horas é o jogo"): entenda pelo contexto. \
Seu tom é calmo, educado e confiante, com um leve humor seco. \
Use as ferramentas que tiver quando elas resolverem o pedido. \
REGRA: só diga que abriu, anotou, agendou ou pesquisou algo se tiver chamado a \
ferramenta para isso AGORA, nesta resposta. Nunca finja uma ação. \
Se precisar de algo que você não tem (clima, notícias, abrir apps), \
diga com honestidade que ainda não tem acesso a isso.
Agora: {hora} {data}"""

# Manda o corpo do pedido e devolve a resposta (JSON) do OpenRouter.
Enviar = Callable[[dict, str], dict]


@dataclass(frozen=True)
class RespostaDaIA:
    fala: str
    # A troca inteira, como a IA viu: pergunta, ferramentas chamadas, resultados e
    # resposta. É isso que vai para a memória (ver memoria.py, sobre fingir ações).
    troca: list[dict]


class CerebroIndisponivelError(RuntimeError):
    """A IA não respondeu (sem internet, chave inválida, sem crédito...)."""


def limpar_para_falar(texto: str) -> str:
    """Tira o que a voz leria em voz alta sem querer: *, #, `, _ e espaços sobrando."""
    sem_marcas = re.sub(r"[*#`_]+", "", texto)
    return re.sub(r"\s+", " ", sem_marcas).strip()


def _enviar_http(corpo: dict, chave: str) -> dict:
    pedido = urllib.request.Request(
        URL,
        data=json.dumps(corpo).encode(),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
            return json.load(resposta)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        raise CerebroIndisponivelError(f"A IA não respondeu ({erro}).") from erro


class Cerebro:
    """Pergunta livre → resposta curta, pronta para ser falada."""

    def __init__(self, chave: str, modelo: str = MODELO, enviar: Enviar = _enviar_http) -> None:
        self._chave = chave
        self._modelo = modelo
        self._enviar = enviar

    def responder(
        self,
        pergunta: str,
        usuario: str,
        agora: datetime | None = None,
        historico: Sequence[dict] = (),
        ferramentas: Sequence[Ferramenta] = (),
    ) -> RespostaDaIA:
        """Responde `pergunta`, lembrando do `historico` e podendo usar `ferramentas`."""
        momento = (agora or datetime.now(FUSO)).astimezone(FUSO)
        mensagens = [
            {
                "role": "system",
                "content": PERSONALIDADE.format(
                    usuario=usuario, hora=falar_hora(momento), data=falar_data(momento)
                ),
            },
            *historico,
            {"role": "user", "content": pergunta},
        ]
        inicio_da_troca = len(mensagens) - 1

        def concluir(fala: str) -> RespostaDaIA:
            final = {"role": "assistant", "content": fala}
            return RespostaDaIA(fala=fala, troca=[*mensagens[inicio_da_troca:], final])

        for _ in range(MAXIMO_DE_RODADAS):
            mensagem = self._perguntar(mensagens, ferramentas)
            chamadas = mensagem.get("tool_calls") or []
            if not chamadas:
                return concluir(limpar_para_falar(mensagem.get("content") or ""))

            resultados = [
                (
                    chamada,
                    mod_ferramentas.executar(
                        ferramentas,
                        chamada["function"]["name"],
                        chamada["function"].get("arguments", ""),
                    ),
                )
                for chamada in chamadas
            ]
            mensagens.append({"role": "assistant", "content": None, "tool_calls": chamadas})
            mensagens += [
                {"role": "tool", "tool_call_id": chamada["id"], "content": resultado.para_ia}
                for chamada, resultado in resultados
            ]
            # Toda ferramenta já trouxe a sua confirmação: fala direto, sem outra viagem à IA.
            if all(resultado.fala for _, resultado in resultados):
                return concluir(" ".join(resultado.fala for _, resultado in resultados))
        raise CerebroIndisponivelError("A IA ficou usando ferramentas sem responder.")

    def _perguntar(self, mensagens: list[dict], ferramentas: Sequence[Ferramenta]) -> dict:
        corpo = {
            "model": self._modelo,
            "max_tokens": MAXIMO_DE_PALAVRAS,
            # Sem "pensar antes": responde ~2x mais rápido com a mesma qualidade.
            "reasoning": {"enabled": False},
            "messages": mensagens,
        }
        if ferramentas:
            corpo["tools"] = mod_ferramentas.no_formato_da_ia(ferramentas)
        resposta = self._enviar(corpo, self._chave)
        try:
            return resposta["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as erro:
            motivo = resposta.get("error", {}).get("message", "resposta sem texto")
            raise CerebroIndisponivelError(f"A IA não respondeu ({motivo}).") from erro


def criar_cerebro() -> Cerebro | None:
    """O cérebro, se houver chave configurada. Sem chave, o Jarvis segue só com os comandos."""
    chave = os.environ.get("OPENROUTER_API_KEY", "").strip()
    return Cerebro(chave) if chave else None
