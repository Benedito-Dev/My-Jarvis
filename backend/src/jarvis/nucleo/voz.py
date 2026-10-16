"""Voz do Jarvis: fala usando o comando `say`, que já vem no macOS."""

import subprocess
import time
from collections.abc import Callable

# Vozes em português instaladas: `say -v '?' | grep pt_BR`.
# Outras (ex.: Felipe) podem ser baixadas em Ajustes > Acessibilidade > Conteúdo Falado.
VOZ_PADRAO = "Luciana"

# Não repete a mesma frase antes deste intervalo (evita o Jarvis "papagaio").
SEGUNDOS_ENTRE_REPETICOES = 6.0

Iniciador = Callable[[list[str]], subprocess.Popen]


class Locutor:
    """Fala frases sem travar o vídeo: o `say` roda em paralelo.

    Regras para não virar bagunça:
    - enquanto está falando, frases novas são ignoradas (a não ser com `interromper=True`);
    - a mesma frase só se repete depois de `SEGUNDOS_ENTRE_REPETICOES`.
    """

    def __init__(
        self,
        voz: str = VOZ_PADRAO,
        iniciar: Iniciador = subprocess.Popen,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._voz = voz
        self._iniciar = iniciar
        self._relogio = relogio
        self._processo: subprocess.Popen | None = None
        self._ultima_frase: str | None = None
        self._ultima_vez = float("-inf")

    def falar(self, frase: str, interromper: bool = False) -> bool:
        """Fala a frase, se as regras permitirem. Retorna True se começou a falar."""
        if self._falando():
            if not interromper:
                return False
            self._processo.terminate()
        repetida = frase == self._ultima_frase
        if repetida and self._relogio() - self._ultima_vez < SEGUNDOS_ENTRE_REPETICOES:
            return False

        self._processo = self._iniciar(["say", "-v", self._voz, frase])
        self._ultima_frase = frase
        self._ultima_vez = self._relogio()
        return True

    def _falando(self) -> bool:
        return self._processo is not None and self._processo.poll() is None
