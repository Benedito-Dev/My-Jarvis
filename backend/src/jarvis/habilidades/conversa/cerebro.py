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
from collections.abc import Callable
from datetime import datetime

from jarvis.habilidades.conversa.comandos import FUSO, falar_data, falar_hora

URL = "https://openrouter.ai/api/v1/chat/completions"
# O DeepSeek mais barato do OpenRouter em out/2026 (~US$ 0,00003 por pergunta).
MODELO = os.environ.get("JARVIS_MODELO_IA", "deepseek/deepseek-v4.1-flash")
TEMPO_LIMITE_S = 30
MAXIMO_DE_PALAVRAS = 300  # tokens de resposta: o Jarvis fala, não escreve redação

PERSONALIDADE = """\
Você é o J.A.R.V.I.S., o assistente pessoal de {usuario}. \
Sua resposta vai ser FALADA em voz alta por um sintetizador, então:
- responda em português do Brasil, em no máximo 3 frases curtas;
- nada de listas, markdown, emojis ou links;
- escreva números como se fala ("384 mil quilômetros", não "384.400 km").
Seu tom é calmo, educado e confiante, com um leve humor seco. \
Se precisar de algo em tempo real que você não tem (clima, notícias, agenda), \
diga com honestidade que ainda não tem acesso a isso.
Agora: {hora} {data}"""

# Manda o corpo do pedido e devolve a resposta (JSON) do OpenRouter.
Enviar = Callable[[dict, str], dict]


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

    def responder(self, pergunta: str, usuario: str, agora: datetime | None = None) -> str:
        momento = (agora or datetime.now(FUSO)).astimezone(FUSO)
        corpo = {
            "model": self._modelo,
            "max_tokens": MAXIMO_DE_PALAVRAS,
            # Sem "pensar antes": responde ~2x mais rápido com a mesma qualidade.
            "reasoning": {"enabled": False},
            "messages": [
                {
                    "role": "system",
                    "content": PERSONALIDADE.format(
                        usuario=usuario, hora=falar_hora(momento), data=falar_data(momento)
                    ),
                },
                {"role": "user", "content": pergunta},
            ],
        }
        resposta = self._enviar(corpo, self._chave)
        try:
            texto = resposta["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as erro:
            motivo = resposta.get("error", {}).get("message", "resposta sem texto")
            raise CerebroIndisponivelError(f"A IA não respondeu ({motivo}).") from erro
        return limpar_para_falar(texto or "")


def criar_cerebro() -> Cerebro | None:
    """O cérebro, se houver chave configurada. Sem chave, o Jarvis segue só com os comandos."""
    chave = os.environ.get("OPENROUTER_API_KEY", "").strip()
    return Cerebro(chave) if chave else None
