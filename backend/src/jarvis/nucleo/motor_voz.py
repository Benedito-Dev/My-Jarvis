"""Qual comando usar para falar em cada sistema operacional.

O Jarvis roda no macOS, no Linux e (em breve) no Windows, e cada um tem o seu
jeito de falar. Este módulo só monta o comando; quem decide *quando* falar é o
`Locutor` (`nucleo/voz.py`).

Como são funções puras (texto → lista de argumentos), dá para testar o comando
de qualquer sistema sem estar nele.
"""

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass

# Voz usada em cada sistema. Pode ser trocada por `JARVIS_VOZ`.
# - macOS: vozes pt-BR instaladas aparecem em `say -v '?' | grep pt_BR`.
# - Linux: o `spd-say` fala por idioma, não por nome de voz. Só existe pt
#   (Portugal) no espeak-ng; pt-BR exigiria outro motor (ver decisão 0012).
VOZ_MACOS = "Luciana"
IDIOMA_LINUX = "pt"


class MotorIndisponivelError(RuntimeError):
    """Este sistema operacional ainda não tem um jeito de falar configurado."""


@dataclass(frozen=True)
class MotorDeVoz:
    """Como falar neste sistema.

    - `falar(frase)`: comando que fala a frase e **só termina quando acabar de
      falar**. O `Locutor` depende disso para saber se ainda está falando.
    - `cancelar`: comando que interrompe a fala em andamento, quando matar o
      processo não basta. `None` quando matar o processo já resolve.
    """

    nome: str
    falar: Callable[[str], list[str]]
    cancelar: list[str] | None = None


def _motor_macos(voz: str) -> MotorDeVoz:
    """O `say` já vem no macOS e dura o tempo da fala (decisão 0008)."""
    return MotorDeVoz(nome="say", falar=lambda frase: ["say", "-v", voz, frase])


def _motor_linux(idioma: str) -> MotorDeVoz:
    """O `spd-say` conversa com o speech-dispatcher, presente na maioria das distros.

    Duas diferenças em relação ao `say` que mudam o comando:

    - `-w` (wait) é obrigatório: sem ele o `spd-say` entrega a frase ao daemon e
      sai na hora, e o `Locutor` acharia que toda fala terminou instantaneamente.
    - matar o `spd-say` não cala o daemon, que continua falando. Por isso
      interromper é um comando separado (`-C`).
    """
    return MotorDeVoz(
        nome="spd-say",
        falar=lambda frase: ["spd-say", "-w", "-l", idioma, frase],
        cancelar=["spd-say", "-C"],
    )


def escolher(plataforma: str = sys.platform) -> MotorDeVoz:
    """Monta o motor de voz da plataforma (os valores de `sys.platform`).

    Levanta `MotorIndisponivelError` em sistemas ainda não cobertos — hoje o
    Windows. Quem chama deve tratar isso seguindo em frente calado: ficar sem
    voz não pode impedir o Jarvis de funcionar.
    """
    if plataforma == "darwin":
        return _motor_macos(os.environ.get("JARVIS_VOZ", VOZ_MACOS))
    if plataforma.startswith("linux"):
        return _motor_linux(os.environ.get("JARVIS_VOZ", IDIOMA_LINUX))
    raise MotorIndisponivelError(
        f"Ainda não sei falar em '{plataforma}'. O Jarvis funciona, mas em silêncio."
    )
