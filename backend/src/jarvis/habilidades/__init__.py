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
        descricao="Ouve e responde por voz",
        situacao=Situacao.EM_BREVE,
    ),
]
