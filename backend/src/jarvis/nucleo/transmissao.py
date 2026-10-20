"""Transmissão: espalha eventos do backend para quem estiver ouvindo (o app).

Usada para a voz: cada fala que começa a tocar vira um evento, e o app faz o
núcleo pulsar junto. Cada assinante tem a sua fila; quem não lê a tempo perde
eventos antigos, mas nunca trava quem publica.
"""

import queue
import threading

MAXIMO_NA_FILA = 50


class Transmissao:
    def __init__(self) -> None:
        self._filas: set[queue.Queue] = set()
        self._trava = threading.Lock()

    def assinar(self) -> queue.Queue:
        fila: queue.Queue = queue.Queue(maxsize=MAXIMO_NA_FILA)
        with self._trava:
            self._filas.add(fila)
        return fila

    def cancelar(self, fila: queue.Queue) -> None:
        with self._trava:
            self._filas.discard(fila)

    def publicar(self, evento: dict) -> None:
        with self._trava:
            filas = list(self._filas)
        for fila in filas:
            try:
                fila.put_nowait(evento)
            except queue.Full:  # assinante lento: perde este, o publicador segue
                pass
