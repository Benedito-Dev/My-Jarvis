"""Memória curta: as últimas trocas da conversa, para a IA entender o contexto.

Com ela, "que dia é hoje?" seguido de "e amanhã?" faz sentido. Fica só na
memória do servidor (nada em disco) e some depois de um tempo parado ou ao
bloquear o Jarvis: a próxima pessoa não herda a conversa da anterior.
"""

import threading
import time
from collections import deque
from collections.abc import Callable

MAXIMO_DE_TROCAS = 8  # pergunta + resposta = 1 troca
ESQUECER_APOS_S = 10 * 60  # dez minutos sem falar e a conversa recomeça


class Memoria:
    def __init__(
        self,
        maximo_de_trocas: int = MAXIMO_DE_TROCAS,
        esquecer_apos_s: float = ESQUECER_APOS_S,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        self._trocas: deque[tuple[str, str]] = deque(maxlen=maximo_de_trocas)
        self._esquecer_apos = esquecer_apos_s
        self._relogio = relogio
        self._ultima_vez = float("-inf")
        self._trava = threading.Lock()

    def lembrar(self, pergunta: str, resposta: str) -> None:
        with self._trava:
            self._expirar()
            self._trocas.append((pergunta, resposta))
            self._ultima_vez = self._relogio()

    def recentes(self) -> list[dict]:
        """As trocas no formato de mensagens da IA, das mais antigas às mais novas."""
        with self._trava:
            self._expirar()
            mensagens = []
            for pergunta, resposta in self._trocas:
                mensagens.append({"role": "user", "content": pergunta})
                mensagens.append({"role": "assistant", "content": resposta})
            return mensagens

    def esquecer(self) -> None:
        with self._trava:
            self._trocas.clear()

    def _expirar(self) -> None:
        if self._relogio() - self._ultima_vez > self._esquecer_apos:
            self._trocas.clear()
