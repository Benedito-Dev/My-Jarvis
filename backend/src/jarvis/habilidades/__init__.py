"""Habilidades do Jarvis: cada uma em sua própria pasta."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Habilidade:
    """O que o Jarvis sabe fazer, do jeito que o usuário vê."""

    id: str
    nome: str
    descricao: str


# Catálogo mostrado na tela inicial. Nova habilidade pronta = nova linha aqui.
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
]
