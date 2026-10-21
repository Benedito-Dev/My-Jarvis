"""Lógica: entende comandos simples no texto transcrito e monta a resposta.

Nada de IA aqui: são regras fixas para o que o Jarvis já sabe fazer (hora,
data, bloquear). Recebe o horário por parâmetro, então dá para testar
qualquer hora do dia sem esperar por ela.
"""

import re
import unicodedata
from collections.abc import Callable
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
BLOQUEANDO = "Bloqueando. Até logo."
# Sem a sessão aberta, o bom dia é só um cumprimento (o resumo tem dados do dono).
BOM_DIA = "Bom dia."
# Respostas que não mudam: o servidor deixa a voz delas pronta ao subir.
FRASES_FIXAS = [NAO_SEI, BLOQUEANDO, BOM_DIA]

# Palavras que pedem para bloquear. Também vale uma palavra *parecida*: o
# Whisper às vezes escreve "bloquia" ou "bokear" para um "bloquear" falado.
PALAVRAS_BLOQUEAR = ["bloquear", "bloqueia", "bloqueie", "bloqueio", "trancar", "tranca"]
SEMELHANCA_MINIMA = 0.7


@dataclass(frozen=True)
class Resposta:
    """O que o Jarvis fala de volta e, se for o caso, o que ele faz."""

    fala: str
    acao: str | None = None  # "bloquear" ou "bom_dia"
    entendeu: bool = True


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem pontuação: "Que HORAS são?" vira "que horas sao"."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]+", " ", sem_acento.lower()).strip()


# Palavras que tiram o pedido dos comandos fixos e mandam para a IA: lembretes
# ("me lembra", "me avisa", "daqui a") e datas que não são hoje ("amanhã", "ontem").
PEDIDO_PARA_A_IA = (
    r"\b(lembr\w*|avis\w*|daqui|timer|alarme|despert\w*|amanha|ontem|depois|semana|"
    r"mes|ano|anos|em \w+ (horas?|minutos?))\b"
)


def as_horas(momento: datetime) -> str:
    """O horário com a preposição certa: "às 10 e 25", "à uma", "ao meio-dia"."""
    hora, minuto = momento.hour, momento.minute
    if hora == 0:
        inicio = "à meia-noite"
    elif hora == 12:
        inicio = "ao meio-dia"
    elif hora == 1:
        inicio = "à uma"
    else:
        inicio = f"às {hora}"
    return inicio if minuto == 0 else f"{inicio} e {minuto}"


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


# Os atalhos locais só respondem quando a frase é SÓ o pedido: palavras de
# cortesia e "Jarvis" podem vir junto, mais nada. "Que horas são?" é atalho;
# "que horas é o jogo do Barcelona?" tem "jogo" e "Barcelona" e vai para a IA.
CORTESIA = {
    "jarvis", "por", "favor", "voce", "sabe", "pode", "poderia", "me", "diz", "dizer",
    "fala", "falar", "ai", "oi", "ola", "agora", "a", "o", "as", "os", "e", "qual",
    "que", "de", "do", "da", "em", "exatamente", "certa", "certo", "hein",
}  # fmt: skip
SO_HORA = CORTESIA | {"hora", "horas", "sao", "son"}
SO_DATA = CORTESIA | {"dia", "data", "hoje", "estamos"}
SO_BLOQUEIO = CORTESIA | {"tela", "computador", "sistema", "tudo", "se", "isso"}
SO_BOM_DIA = CORTESIA | {"bom", "dia", "resumo", "briefing", "meu", "senhor"}


def so_tem(
    frase: str, permitidas: set[str], extras: Callable[[str], bool] = lambda _: False
) -> bool:
    """Todas as palavras da frase são permitidas (ou passam no teste `extras`)?

    Letras soltas não contam: o Whisper às vezes "gagueja" ("B bloquear").
    """
    return all(
        len(palavra) <= 1 or palavra in permitidas or extras(palavra) for palavra in frase.split()
    )


def parece_bloquear(palavra: str) -> bool:
    """A palavra é, ou parece, "bloquear" (o Whisper às vezes escreve "bloquia")."""
    return bool(get_close_matches(palavra, PALAVRAS_BLOQUEAR, n=1, cutoff=SEMELHANCA_MINIMA))


def pede_bloqueio(frase: str) -> bool:
    """A frase é um pedido para bloquear, e só isso? ("como bloquear o Instagram" não é.)"""
    palavras = frase.split()
    return any(parece_bloquear(p) for p in palavras) and so_tem(frase, SO_BLOQUEIO, parece_bloquear)


def pede_bom_dia(frase: str) -> bool:
    """'Bom dia', 'Jarvis, bom dia', 'resumo do dia' ou 'briefing', e só isso."""
    pediu = re.search(r"\b(bom dia|resumo do dia|briefing)\b", frase)
    return bool(pediu) and so_tem(frase, SO_BOM_DIA)


def responder(texto: str, agora: datetime | None = None) -> Resposta | None:
    """A resposta para o que foi dito, ou None se não foi dito nada."""
    frase = normalizar(texto)
    if not frase:
        return None
    momento = (agora or datetime.now(FUSO)).astimezone(FUSO)

    # "Me lembra de bloquear a porta daqui a 2 horas" fala de bloquear e de horas,
    # mas é um pedido para a IA (que agenda lembretes), não um comando daqui.
    if re.search(PEDIDO_PARA_A_IA, frase):
        return Resposta(fala=NAO_SEI, entendeu=False)

    if pede_bloqueio(frase):
        return Resposta(fala=BLOQUEANDO, acao="bloquear")
    if pede_bom_dia(frase):
        return Resposta(fala=BOM_DIA, acao="bom_dia")
    palavras = set(frase.split())
    if palavras & {"dia", "data"} and so_tem(frase, SO_DATA):
        return Resposta(fala=falar_data(momento))
    if palavras & {"hora", "horas"} and so_tem(frase, SO_HORA):
        return Resposta(fala=falar_hora(momento))
    return Resposta(fala=NAO_SEI, entendeu=False)
