"""Habilidades do Jarvis: cada uma em sua própria pasta."""

from dataclasses import dataclass
from enum import StrEnum


class Situacao(StrEnum):
    PRONTA = "pronta"
    EM_BREVE = "em_breve"


@dataclass(frozen=True)
class Habilidade:
    """O que o Jarvis sabe fazer, do jeito que o usuário vê."""

    id: str
    nome: str
    descricao: str
    situacao: Situacao = Situacao.PRONTA


# Catálogo mostrado na tela inicial. Nova habilidade = nova linha aqui.
HABILIDADES = [
    Habilidade(
        id="desbloqueio_facial",
        nome="Desbloqueio facial",
        descricao="Reconhece o rosto do dono pela câmera",
    ),
    Habilidade(
        id="voz",
        nome="Voz",
        descricao="Fala em voz alta",
    ),
    Habilidade(
        id="conversa",
        nome="Conversa",
        descricao="Conversa por voz: comandos e perguntas livres (IA)",
    ),
    Habilidade(
        id="bom_dia",
        nome="Bom dia",
        descricao="Resumo do dia: clima, lembretes de hoje e notícias",
    ),
    Habilidade(
        id="escuta",
        nome="Escuta",
        descricao='Chamar pelo nome, sem tecla: "Jarvis, que horas são?"',
    ),
]
