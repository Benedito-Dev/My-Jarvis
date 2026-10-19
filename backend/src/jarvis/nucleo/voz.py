"""Voz do Jarvis: fala em voz alta, usando o motor de voz do sistema.

*Qual* comando fala em cada sistema é assunto do `nucleo/motor_voz.py`.
Aqui ficam as regras de *quando* falar.
"""

import os
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable

from jarvis.nucleo.motor_voz import MotorDeVoz, MotorIndisponivelError, escolher
from jarvis.nucleo.voz_piper import VozPiper

# Não repete a mesma frase antes deste intervalo (evita o Jarvis "papagaio").
SEGUNDOS_ENTRE_REPETICOES = 6.0

Iniciador = Callable[[list[str]], subprocess.Popen]


class _Detectar:
    """Marca "descubra o motor desta máquina".

    Precisa ser diferente de `None`, que significa "fique mudo de propósito".
    """


DETECTAR = _Detectar()


class Locutor:
    """Fala frases sem travar o vídeo: o comando de fala roda em paralelo.

    Regras para não virar bagunça:
    - enquanto está falando, frases novas são ignoradas (a não ser com `interromper=True`);
    - a mesma frase só se repete depois de `SEGUNDOS_ENTRE_REPETICOES`.

    Em sistema sem motor de voz (hoje o Windows), o Locutor fica mudo: `falar`
    devolve False e o Jarvis segue funcionando normalmente.
    """

    def __init__(
        self,
        motor: MotorDeVoz | None | _Detectar = DETECTAR,
        iniciar: Iniciador = subprocess.Popen,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._motor = _motor_do_sistema() if isinstance(motor, _Detectar) else motor
        self._iniciar = iniciar
        self._relogio = relogio
        self._processo: subprocess.Popen | None = None
        self._ultima_frase: str | None = None
        self._ultima_vez = float("-inf")

    @property
    def muda(self) -> bool:
        """True quando este sistema não sabe falar."""
        return self._motor is None

    def falar(self, frase: str, interromper: bool = False) -> bool:
        """Fala a frase, se as regras permitirem. Retorna True se começou a falar."""
        if self._motor is None:
            return False
        if self._falando():
            if not interromper:
                return False
            self._calar()
        repetida = frase == self._ultima_frase
        if repetida and self._relogio() - self._ultima_vez < SEGUNDOS_ENTRE_REPETICOES:
            return False

        try:
            comando = self._motor.falar(frase)
        except Exception as erro:  # ex.: sem internet para baixar o modelo do Piper
            print(f"Não consegui preparar a fala ({erro}).")
            return False
        self._processo = self._iniciar(comando)
        self._ultima_frase = frase
        self._ultima_vez = self._relogio()
        return True

    def preparar(self, frases: Iterable[str]) -> None:
        """Deixa frases prontas antes, para saírem sem espera (só o Piper precisa)."""
        if self._motor is not None and self._motor.preparar is not None:
            self._motor.preparar(frases)

    def _falando(self) -> bool:
        return self._processo is not None and self._processo.poll() is None

    def _calar(self) -> None:
        """Interrompe a fala atual.

        Matar o processo basta no macOS, mas não no Linux: lá o `spd-say` só
        entrega a frase a um daemon, que continua falando. Por isso o motor pode
        pedir um comando extra de cancelamento.
        """
        if self._processo is not None:
            self._processo.terminate()
        if self._motor is not None and self._motor.cancelar is not None:
            self._iniciar(self._motor.cancelar)


def _motor_do_sistema() -> MotorDeVoz | None:
    """Motor desta máquina, ou None se ela ainda não sabe falar.

    Primeiro a voz Piper (a mesma nos três sistemas); se não der para tocar
    áudio, a voz do próprio sistema. Também fica mudo se o programa do motor
    não estiver instalado (ex.: Linux sem `spd-say`): ficar sem voz não pode
    derrubar um desbloqueio.
    """
    if os.environ.get("JARVIS_MUDO"):  # ex.: nos testes, que não podem sair falando
        return None
    for voz_piper in (VozPiper(), None):
        try:
            motor = escolher(voz_piper=voz_piper)
        except MotorIndisponivelError:
            continue
        if shutil.which(motor.programa):
            return motor
    return None
