"""As "mãos" do Jarvis: ferramentas que a IA pode decidir usar.

Cada ferramenta tem um nome, uma descrição (é por ela que a IA sabe quando usar)
e os parâmetros que espera, no formato de "function calling" do OpenRouter.
Nova ferramenta = nova função aqui que devolve uma `Ferramenta`.
"""

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from jarvis.habilidades.conversa.comandos import as_horas
from jarvis.habilidades.lembretes.agenda import Agenda, LembreteInvalidoError


@dataclass(frozen=True)
class Resultado:
    """O que a ferramenta fez.

    - `para_ia`: o resultado contado à IA, se ela precisar continuar a resposta;
    - `fala`: uma confirmação já pronta para falar. Se toda ferramenta usada
      trouxer a sua, não é preciso voltar à IA (~2 s a menos).
    """

    para_ia: str
    fala: str | None = None


@dataclass(frozen=True)
class Ferramenta:
    nome: str
    descricao: str
    parametros: dict  # JSON Schema
    executar: Callable[[dict], Resultado]


def no_formato_da_ia(ferramentas: Iterable[Ferramenta]) -> list[dict]:
    """A lista de ferramentas como a IA espera receber."""
    return [
        {
            "type": "function",
            "function": {
                "name": f.nome,
                "description": f.descricao,
                "parameters": f.parametros,
            },
        }
        for f in ferramentas
    ]


def executar(ferramentas: Iterable[Ferramenta], nome: str, argumentos: str) -> Resultado:
    """Roda a ferramenta que a IA pediu. Erros viram resultado, para a IA explicar."""
    por_nome = {f.nome: f for f in ferramentas}
    if nome not in por_nome:
        return Resultado(para_ia=f"Erro: não existe a ferramenta {nome!r}.")
    try:
        parametros = json.loads(argumentos or "{}")
    except json.JSONDecodeError:
        return Resultado(para_ia="Erro: os parâmetros não vieram em JSON válido.")
    try:
        return por_nome[nome].executar(parametros)
    except (KeyError, TypeError, ValueError) as erro:
        return Resultado(para_ia=f"Erro ao usar {nome}: {erro}")


# --- Lembretes ------------------------------------------------------------------


def lembrete(agenda: Agenda) -> Ferramenta:
    def criar(parametros: dict) -> Resultado:
        try:
            criado = agenda.criar(float(parametros["daqui_a_minutos"]), parametros["texto"])
        except LembreteInvalidoError as erro:
            return Resultado(para_ia=f"Não agendado: {erro}")
        horario = as_horas(criado.quando)
        return Resultado(
            para_ia=f"Lembrete agendado para {horario}: {criado.texto}.",
            fala=f"Certo. Te aviso {horario}.",
        )

    return Ferramenta(
        nome="criar_lembrete",
        descricao=(
            "Agenda um lembrete que o Jarvis fala em voz alta depois de alguns minutos. "
            "Use quando pedirem para lembrar ou avisar de algo mais tarde. "
            "Para um horário (ex.: às 10 e meia), calcule os minutos a partir de agora."
        ),
        parametros={
            "type": "object",
            "properties": {
                "daqui_a_minutos": {
                    "type": "number",
                    "description": "Em quantos minutos avisar (de 1 a 1440).",
                },
                "texto": {
                    "type": "string",
                    "description": "O que lembrar, curto (ex.: 'ligar pro dentista').",
                },
            },
            "required": ["daqui_a_minutos", "texto"],
        },
        executar=criar,
    )


def listar_lembretes(agenda: Agenda) -> Ferramenta:
    def listar(_parametros: dict) -> Resultado:
        pendentes = agenda.pendentes()
        if not pendentes:
            return Resultado(para_ia="Nenhum lembrete pendente.")
        itens = "; ".join(f"{as_horas(lem.quando)}: {lem.texto}" for lem in pendentes)
        return Resultado(para_ia=f"Lembretes pendentes: {itens}.")

    return Ferramenta(
        nome="listar_lembretes",
        descricao="Lista os lembretes que ainda vão tocar. Use quando perguntarem pelos lembretes.",
        parametros={"type": "object", "properties": {}},
        executar=listar,
    )
