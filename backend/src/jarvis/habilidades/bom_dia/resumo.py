"""Lógica: monta o resumo do dia, um assunto de cada vez.

Sem IA: as frases são montadas aqui, a partir dos dados. Assim o bom dia sai
rápido, funciona sem a chave da IA e sempre traz os três assuntos. Cada
assunto vira uma fala e um cartão na tela. Quem fala e mostra é a API.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from jarvis.habilidades.clima import previsao
from jarvis.habilidades.conversa.comandos import FUSO, as_horas
from jarvis.habilidades.lembretes import agenda as mod_agenda
from jarvis.habilidades.lembretes.agenda import Lembrete
from jarvis.habilidades.noticias import manchetes

MANCHETES_NO_BOM_DIA = 3
LEMBRETES_FALADOS = 3  # mais que isso, o cartão mostra e a fala só conta


@dataclass(frozen=True)
class Parte:
    """Um assunto pronto: o que falar e, se houver, o cartão da tela."""

    fala: str
    cartao: dict | None = None


@dataclass(frozen=True)
class Assunto:
    """Um assunto do resumo, ainda por buscar. `ferramenta` é o nome que a tela
    conhece para mostrar o progresso ("Consultando o clima...")."""

    ferramenta: str
    preparar: Callable[[], Parte]


def saudacao(usuario: str, agora: datetime) -> str:
    """'Bom dia, Benedito.', ou boa tarde / boa noite, conforme a hora."""
    hora = agora.astimezone(FUSO).hour
    cumprimento = "Bom dia" if hora < 12 else "Boa tarde" if hora < 18 else "Boa noite"
    return f"{cumprimento}, {usuario}."


def assuntos(
    pendentes: Callable[[], list[Lembrete]],
    agora: datetime,
    obter_clima: previsao.ObterJson = previsao._obter_json,
    obter_noticias: manchetes.ObterFeed = manchetes._obter_feed,
) -> list[Assunto]:
    """Os assuntos do resumo, na ordem em que são falados."""
    return [
        Assunto("clima", lambda: parte_do_clima(obter_clima)),
        Assunto("listar_lembretes", lambda: parte_dos_lembretes(pendentes(), agora)),
        Assunto("noticias", lambda: parte_das_noticias(obter_noticias)),
    ]


def parte_do_clima(obter: previsao.ObterJson = previsao._obter_json) -> Parte:
    cidade = previsao.cidade_padrao()
    if not cidade:
        return Parte("Não sei a sua cidade, então fico devendo o clima.")
    try:
        lugar, dados = previsao.consultar(cidade, obter=obter)
    except previsao.ClimaIndisponivelError:
        return Parte("Não consegui ver o clima agora.")
    agora, hoje = dados["current"], dados["daily"]
    ceu = previsao.CEU.get(agora["weather_code"], "tempo indefinido")
    chuva = hoje["precipitation_probability_max"][0]
    fala = (
        f"Em {lugar.nome}, agora faz {round(agora['temperature_2m'])} graus, {ceu}. "
        f"A máxima hoje é de {round(hoje['temperature_2m_max'][0])}"
    )
    fala += f", com {chuva}% de chance de chuva." if chuva else "."
    return Parte(fala, previsao.cartao(lugar, dados))


def parte_dos_lembretes(pendentes: list[Lembrete], agora: datetime) -> Parte:
    """Só os de hoje: a agenda guarda até 24 h, então pode haver de amanhã."""
    dia = agora.astimezone(FUSO).date()
    de_hoje = [lem for lem in pendentes if lem.quando.astimezone(FUSO).date() == dia]
    cartao = mod_agenda.cartao("Lembretes de hoje", de_hoje)
    if not de_hoje:
        return Parte("Nenhum lembrete para hoje.", {**cartao, "titulo": "Nada agendado"})
    lidos = [f"{as_horas(lem.quando)}, {lem.texto}" for lem in de_hoje[:LEMBRETES_FALADOS]]
    if len(de_hoje) == 1:
        return Parte(f"Você tem um lembrete hoje: {lidos[0]}.", cartao)
    lista = "; ".join(lidos[:-1]) + f"; e {lidos[-1]}"
    if len(de_hoje) > LEMBRETES_FALADOS:
        return Parte(f"Você tem {len(de_hoje)} lembretes hoje. Os próximos: {lista}.", cartao)
    return Parte(f"Você tem {len(de_hoje)} lembretes hoje: {lista}.", cartao)


def parte_das_noticias(obter: manchetes.ObterFeed = manchetes._obter_feed) -> Parte:
    try:
        lista = manchetes.manchetes(MANCHETES_NO_BOM_DIA, obter=obter)
    except manchetes.NoticiasIndisponiveisError:
        return Parte("Não consegui ler as notícias agora.")
    if not lista:
        return Parte("Não achei notícias agora.")
    titulos = " ".join(f"{m.titulo.rstrip('.')}." for m in lista)
    return Parte(
        f"Nas notícias: {titulos} Quer que eu detalhe alguma delas?", manchetes.cartao(lista)
    )
