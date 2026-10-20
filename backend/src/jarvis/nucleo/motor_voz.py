"""Qual comando usar para falar em cada sistema operacional.

A voz principal é o Piper (`voz_piper.py`): a mesma nos três sistemas. Ele gera
um .wav, e o que muda de sistema para sistema é só o programa que toca o
arquivo. Sem Piper, cada sistema usa a voz que já tem (`say`, `spd-say`).

Este módulo só monta comandos; quem decide *quando* falar é o `Locutor`
(`nucleo/voz.py`). Como são funções puras, dá para testar o comando de
qualquer sistema sem estar nele.
"""

import os
import shutil
import sys
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jarvis.nucleo.voz_piper import VozPiper


def envelope_do_arquivo(arquivo: Path) -> list[float]:
    from jarvis.nucleo.voz_piper import envelope  # numpy só quando for usar

    return envelope(arquivo)


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
    - `programa`: o executável que precisa existir na máquina para falar.
    - `preparar(frases)`: deixa frases prontas antes (só o Piper usa).
    - `envelope(frase)`: o volume da frase a cada 40 ms, de 0 a 1 (só o Piper,
      que gera o áudio aqui; com `say`/`spd-say` não há como medir).
    """

    nome: str
    falar: Callable[[str], list[str]]
    programa: str
    cancelar: list[str] | None = None
    preparar: Callable[[Iterable[str]], None] | None = None
    envelope: Callable[[str], list[float]] | None = None


def _motor_macos(voz: str) -> MotorDeVoz:
    """O `say` já vem no macOS e dura o tempo da fala (decisão 0008)."""
    return MotorDeVoz(nome="say", programa="say", falar=lambda frase: ["say", "-v", voz, frase])


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
        programa="spd-say",
        falar=lambda frase: ["spd-say", "-w", "-l", idioma, frase],
        cancelar=["spd-say", "-C"],
    )


# Tocadores de .wav no Linux, do mais comum ao menos: PulseAudio, ALSA, PipeWire.
TOCADORES_LINUX = (["paplay"], ["aplay", "-q"], ["pw-play"])


def comando_tocar(
    plataforma: str, existe: Callable[[str], str | None] = shutil.which
) -> Callable[[Path], list[str]]:
    """O comando que toca um .wav e só termina quando o áudio acabar."""
    if plataforma == "darwin":
        return lambda arquivo: ["afplay", str(arquivo)]
    if plataforma.startswith("linux"):
        for tocador in TOCADORES_LINUX:
            if existe(tocador[0]):
                return lambda arquivo, tocador=tocador: [*tocador, str(arquivo)]
        raise MotorIndisponivelError("Nenhum tocador de áudio (paplay, aplay, pw-play).")
    if plataforma == "win32":
        # O SoundPlayer do .NET já vem no Windows; PlaySync espera o áudio acabar.
        return lambda arquivo: [
            "powershell",
            "-NoProfile",
            "-Command",
            f"(New-Object Media.SoundPlayer '{arquivo}').PlaySync()",
        ]
    raise MotorIndisponivelError(f"Não sei tocar áudio em '{plataforma}'.")


def _motor_piper(
    voz: "VozPiper", plataforma: str, existe: Callable[[str], str | None]
) -> MotorDeVoz:
    tocar = comando_tocar(plataforma, existe)
    return MotorDeVoz(
        nome="piper",
        programa=tocar(Path("x.wav"))[0],
        falar=lambda frase: tocar(voz.arquivo_da_frase(frase)),
        preparar=voz.preparar,
        envelope=lambda frase: envelope_do_arquivo(voz.arquivo_da_frase(frase)),
    )


def escolher(
    plataforma: str = sys.platform,
    voz_piper: "VozPiper | None" = None,
    existe: Callable[[str], str | None] = shutil.which,
) -> MotorDeVoz:
    """Monta o motor de voz da plataforma (os valores de `sys.platform`).

    Com `voz_piper`, é a voz Piper nos três sistemas. Sem ela, a voz do sistema;
    aí levanta `MotorIndisponivelError` no Windows, que não tem uma pronta.
    Quem chama deve tratar isso seguindo em frente calado: ficar sem voz não
    pode impedir o Jarvis de funcionar.
    """
    if voz_piper is not None:
        return _motor_piper(voz_piper, plataforma, existe)
    if plataforma == "darwin":
        return _motor_macos(os.environ.get("JARVIS_VOZ", VOZ_MACOS))
    if plataforma.startswith("linux"):
        return _motor_linux(os.environ.get("JARVIS_VOZ", IDIOMA_LINUX))
    raise MotorIndisponivelError(
        f"Ainda não sei falar em '{plataforma}'. O Jarvis funciona, mas em silêncio."
    )
