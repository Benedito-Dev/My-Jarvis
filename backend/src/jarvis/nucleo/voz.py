"""Voz do Jarvis: fala em voz alta, usando o motor de voz do sistema.

*Qual* comando fala em cada sistema é assunto do `nucleo/motor_voz.py`.
Aqui ficam as regras de *quando* falar.
"""

import os
import shutil
import subprocess
import threading
import time
from collections import deque
from collections.abc import Callable, Iterable

from jarvis.nucleo.motor_voz import MotorDeVoz, MotorIndisponivelError, escolher
from jarvis.nucleo.voz_piper import VozPiper

# Não repete a mesma frase antes deste intervalo (evita o Jarvis "papagaio").
SEGUNDOS_ENTRE_REPETICOES = 6.0

Iniciador = Callable[[list[str]], subprocess.Popen]
# Roda uma tarefa sem travar quem chamou (nos testes, roda na hora).
EmFundo = Callable[[Callable[[], None]], None]


def _em_uma_thread(tarefa: Callable[[], None]) -> None:
    threading.Thread(target=tarefa, daemon=True).start()


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

    Para respostas longas há a fila (`enfileirar`): as frases tocam uma depois da
    outra, e a próxima já vai sendo gerada enquanto a atual toca. Interromper
    esvazia a fila.

    Em sistema sem motor de voz (hoje o Windows), o Locutor fica mudo: `falar`
    devolve False e o Jarvis segue funcionando normalmente.
    """

    def __init__(
        self,
        motor: MotorDeVoz | None | _Detectar = DETECTAR,
        iniciar: Iniciador = subprocess.Popen,
        relogio: Callable[[], float] = time.monotonic,
        em_fundo: EmFundo = _em_uma_thread,
    ) -> None:
        self._motor = _motor_do_sistema() if isinstance(motor, _Detectar) else motor
        self._iniciar = iniciar
        self._relogio = relogio
        self._em_fundo = em_fundo
        self._fila: deque[str] = deque()
        self._tocando_fila = False
        # Muda a cada interrupção: a fila antiga percebe e para de tocar.
        self._geracao = 0
        self._geracao_da_fila = -1  # de qual geração é a fila que está tocando
        self._observador: Callable[[str, list[float] | None], None] | None = None
        self._trava = threading.Lock()
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
        if interromper:
            with self._trava:
                self._fila.clear()
                self._geracao += 1
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
        self._avisar_que_comecou(frase)
        return True

    def observar(self, observador: Callable[[str, list[float] | None], None]) -> None:
        """Chama `observador(frase, envelope)` sempre que uma fala COMEÇA a tocar.
        O envelope (volume a cada 40 ms) vem quando o motor sabe medir; senão, None."""
        self._observador = observador

    def _avisar_que_comecou(self, frase: str) -> None:
        if self._observador is None:
            return
        try:
            envelope = self._motor.envelope(frase) if self._motor.envelope else None
            self._observador(frase, envelope)
        except Exception as erro:  # observar nunca pode calar o Jarvis
            print(f"Não consegui avisar a fala ({erro}).", flush=True)

    def calar(self) -> None:
        """Para a fala atual e esvazia a fila."""
        with self._trava:
            self._fila.clear()
            self._geracao += 1
        if self._falando():
            self._calar()

    def enfileirar(self, frase: str) -> None:
        """Fala `frase` depois das que já estão na fila (respostas em pedaços)."""
        if self._motor is None:
            return
        # Já começa a gerar o áudio desta frase, enquanto as anteriores tocam.
        self._em_fundo(lambda: self._preparar_quieto([frase]))
        with self._trava:
            self._fila.append(frase)
            # Já há quem toque a fila desta geração. (Se a que está tocando é de
            # antes de uma interrupção, ela vai parar sozinha: liga uma nova.)
            if self._tocando_fila and self._geracao_da_fila == self._geracao:
                return
            self._tocando_fila = True
            self._geracao_da_fila = geracao = self._geracao
        self._em_fundo(lambda: self._tocar_fila(geracao))

    def _tocar_fila(self, geracao: int) -> None:
        while True:
            with self._trava:
                if not self._fila or geracao != self._geracao:
                    self._parar_de_tocar(geracao)
                    return
                frase = self._fila.popleft()
            try:
                comando = self._motor.falar(frase)
            except Exception as erro:
                print(f"Não consegui preparar a fala ({erro}).")
                continue
            with self._trava:
                if geracao != self._geracao:  # interromperam enquanto gerava
                    self._parar_de_tocar(geracao)
                    return
                self._processo = self._iniciar(comando)
                processo = self._processo
            self._ultima_frase, self._ultima_vez = frase, self._relogio()
            self._avisar_que_comecou(frase)
            processo.wait()

    def _parar_de_tocar(self, geracao: int) -> None:
        """Chamar com a trava. Só desliga a marca se for a fila atual que parou."""
        if geracao == self._geracao_da_fila:
            self._tocando_fila = False

    def _preparar_quieto(self, frases: list[str]) -> None:
        try:
            self.preparar(frases)
        except Exception:  # a fila tenta de novo na hora de tocar
            pass

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
