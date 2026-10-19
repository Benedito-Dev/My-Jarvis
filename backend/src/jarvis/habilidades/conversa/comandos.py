"""Lógica: entende comandos simples no texto transcrito e monta a resposta.

Nada de IA aqui: são regras fixas para o que o Jarvis já sabe fazer (hora,
data, bloquear). Recebe o horário por parâmetro, então dá para testar
qualquer hora do dia sem esperar por ela.
"""

import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from difflib import get_close_matches
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")  # no Windows, vem do pacote tzdata

DIAS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira",
        "sábado", "domingo"]  # fmt: skip
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]  # fmt: skip

NAO_SEI = "Ainda não sei fazer isso."

# Palavras que pedem para bloquear. Também vale uma palavra *parecida*: o
# Whisper às vezes escreve "bloquia" ou "bokear" para um "bloquear" falado.
PALAVRAS_BLOQUEAR = ["bloquear", "bloqueia", "bloqueie", "bloqueio", "trancar", "tranca"]
SEMELHANCA_MINIMA = 0.7


@dataclass(frozen=True)
class Resposta:
    """O que o Jarvis fala de volta e, se for o caso, o que ele faz."""

    fala: str
    acao: str | None = None  # hoje só "bloquear"
    entendeu: bool = True


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem pontuação: "Que HORAS são?" vira "que horas sao"."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento.lower()).strip()


def falar_hora(agora: datetime) -> str:
    """A hora do jeito que se fala: "São 13 horas e 57", "É meio-dia em ponto"."""
    hora, minuto = agora.hour, agora.minute
    if hora == 0:
        inicio = "É meia-noite"
    elif hora == 12:
        inicio = "É meio-dia"
    elif hora == 1:
        inicio = "É uma hora"
    else:
        inicio = f"São {hora} horas"

    if minuto == 0:
        return f"{inicio} em ponto."
    if minuto == 1:
        return f"{inicio} e 1 minuto."
    return f"{inicio} e {minuto}."


def falar_data(agora: datetime) -> str:
    """'Hoje é segunda-feira, 19 de outubro.'"""
    return f"Hoje é {DIAS[agora.weekday()]}, {agora.day} de {MESES[agora.month - 1]}."


def pede_bloqueio(frase: str) -> bool:
    """Alguma palavra da frase (já normalizada) é, ou parece, "bloquear"?"""
    return any(
        get_close_matches(palavra, PALAVRAS_BLOQUEAR, n=1, cutoff=SEMELHANCA_MINIMA)
        for palavra in frase.split()
    )


def responder(texto: str, agora: datetime | None = None) -> Resposta | None:
    """A resposta para o que foi dito, ou None se não foi dito nada."""
    frase = normalizar(texto)
    if not frase:
        return None
    momento = (agora or datetime.now(FUSO)).astimezone(FUSO)

    if pede_bloqueio(frase):
        return Resposta(fala="Bloqueando. Até logo.", acao="bloquear")
    if re.search(r"\b(que dia|data|dia e hoje|dia de hoje|dia hoje)\b", frase):
        return Resposta(fala=falar_data(momento))
    if re.search(r"\bhoras?\b", frase):
        return Resposta(fala=falar_hora(momento))
    return Resposta(fala=NAO_SEI, entendeu=False)
