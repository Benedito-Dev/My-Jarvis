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
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import datetime

from jarvis.habilidades.conversa import ferramentas as mod_ferramentas
from jarvis.habilidades.conversa.comandos import FUSO, falar_data, falar_hora
from jarvis.habilidades.conversa.ferramentas import Ferramenta
from jarvis.habilidades.conversa.frases import fatiar

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

# Manda o corpo do pedido e entrega, em fluxo, os pedaços da resposta do OpenRouter.
Enviar = Callable[[dict, str], Iterator[dict]]


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


def _enviar_http(corpo: dict, chave: str) -> Iterator[dict]:
    """Pede a resposta em fluxo (stream) e entrega cada pedaço que chega."""
    pedido = urllib.request.Request(
        URL,
        data=json.dumps({**corpo, "stream": True}).encode(),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(pedido, timeout=TEMPO_LIMITE_S) as resposta:
            for linha in resposta:
                # Formato SSE: "data: {...}"; ": ..." são comentários de "ainda pensando".
                linha = linha.decode("utf-8").strip()
                if not linha.startswith("data:"):
                    continue
                dados = linha.removeprefix("data:").strip()
                if dados == "[DONE]":
                    return
                yield json.loads(dados)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as erro:
        raise CerebroIndisponivelError(f"A IA não respondeu ({erro}).") from erro


@dataclass(frozen=True)
class Frase:
    """Um pedaço da resposta, pronto para falar (e mostrar) enquanto o resto chega."""

    texto: str


@dataclass(frozen=True)
class Fim:
    resposta: RespostaDaIA


class Cerebro:
    """Pergunta livre → resposta curta, pronta para ser falada, frase a frase."""

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
        """A resposta inteira de uma vez (por cima do fluxo)."""
        for evento in self.responder_em_fluxo(pergunta, usuario, agora, historico, ferramentas):
            if isinstance(evento, Fim):
                return evento.resposta
        raise CerebroIndisponivelError("A IA terminou sem resposta.")

    def responder_em_fluxo(
        self,
        pergunta: str,
        usuario: str,
        agora: datetime | None = None,
        historico: Sequence[dict] = (),
        ferramentas: Sequence[Ferramenta] = (),
    ) -> Iterator[Frase | Fim]:
        """Responde `pergunta` aos pedaços: cada `Frase` sai assim que fecha, e no
        fim vem um `Fim` com a resposta inteira (e a troca, para a memória).
        Lembra do `historico` e pode usar `ferramentas`.
        """
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
        falado: list[str] = []

        def concluir() -> Fim:
            fala = " ".join(falado)
            final = {"role": "assistant", "content": fala}
            return Fim(RespostaDaIA(fala=fala, troca=[*mensagens[inicio_da_troca:], final]))

        for _ in range(MAXIMO_DE_RODADAS):
            pendente = ""
            chamadas: dict[int, dict] = {}
            for pedaco in self._enviar(self._corpo(mensagens, ferramentas), self._chave):
                if "error" in pedaco:
                    motivo = pedaco["error"].get("message", "erro desconhecido")
                    raise CerebroIndisponivelError(f"A IA não respondeu ({motivo}).")
                delta = (pedaco.get("choices") or [{}])[0].get("delta") or {}
                pendente += delta.get("content") or ""
                prontas, pendente = fatiar(pendente)
                for frase in prontas:
                    falado.append(limpar_para_falar(frase))
                    yield Frase(falado[-1])
                for parte in delta.get("tool_calls") or []:
                    _juntar_chamada(chamadas, parte)

            if pendente.strip():  # o fim do texto não termina com ". "
                falado.append(limpar_para_falar(pendente))
                yield Frase(falado[-1])
            if not chamadas:
                yield concluir()
                return

            lista = [chamadas[i] for i in sorted(chamadas)]
            resultados = [
                (
                    chamada,
                    mod_ferramentas.executar(
                        ferramentas, chamada["function"]["name"], chamada["function"]["arguments"]
                    ),
                )
                for chamada in lista
            ]
            mensagens.append({"role": "assistant", "content": None, "tool_calls": lista})
            mensagens += [
                {"role": "tool", "tool_call_id": chamada["id"], "content": resultado.para_ia}
                for chamada, resultado in resultados
            ]
            # Toda ferramenta já trouxe a sua confirmação: fala direto, sem outra viagem à IA.
            if all(resultado.fala for _, resultado in resultados):
                for _, resultado in resultados:
                    falado.append(resultado.fala)
                    yield Frase(resultado.fala)
                yield concluir()
                return
        raise CerebroIndisponivelError("A IA ficou usando ferramentas sem responder.")

    def _corpo(self, mensagens: list[dict], ferramentas: Sequence[Ferramenta]) -> dict:
        corpo = {
            "model": self._modelo,
            "max_tokens": MAXIMO_DE_PALAVRAS,
            # Sem "pensar antes": responde ~2x mais rápido com a mesma qualidade.
            "reasoning": {"enabled": False},
            "messages": mensagens,
        }
        if ferramentas:
            corpo["tools"] = mod_ferramentas.no_formato_da_ia(ferramentas)
        return corpo


def _juntar_chamada(chamadas: dict[int, dict], parte: dict) -> None:
    """No fluxo, uma chamada de ferramenta chega picada: o nome numa parte, os
    argumentos em várias. Junta tudo pelo índice da chamada."""
    chamada = chamadas.setdefault(
        parte.get("index", 0),
        {"id": "", "type": "function", "function": {"name": "", "arguments": ""}},
    )
    chamada["id"] = parte.get("id") or chamada["id"]
    funcao = parte.get("function") or {}
    chamada["function"]["name"] += funcao.get("name") or ""
    chamada["function"]["arguments"] += funcao.get("arguments") or ""


def criar_cerebro() -> Cerebro | None:
    """O cérebro, se houver chave configurada. Sem chave, o Jarvis segue só com os comandos."""
    chave = os.environ.get("OPENROUTER_API_KEY", "").strip()
    return Cerebro(chave) if chave else None
