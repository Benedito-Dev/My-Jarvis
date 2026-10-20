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
# Resultado de ferramenta guardado na memória: o bastante para o contexto, sem
# carregar páginas de busca inteiras em toda pergunta seguinte.
MAXIMO_DE_LETRAS_DE_FERRAMENTA = 300


class Memoria:
    def __init__(
        self,
        maximo_de_trocas: int = MAXIMO_DE_TROCAS,
        esquecer_apos_s: float = ESQUECER_APOS_S,
        relogio: Callable[[], float] = time.monotonic,
    ) -> None:
        # Cada troca é a lista de mensagens dela: pergunta, chamadas de ferramenta,
        # resultados e a resposta. Guardar as ferramentas importa: se a memória só
        # tivesse o texto ("Abrindo o Spotify."), a IA aprenderia a FINGIR a ação.
        self._trocas: deque[list[dict]] = deque(maxlen=maximo_de_trocas)
        self._esquecer_apos = esquecer_apos_s
        self._relogio = relogio
        self._ultima_vez = float("-inf")
        self._trava = threading.Lock()

    def lembrar(self, pergunta: str, resposta: str) -> None:
        """Uma troca simples, sem ferramentas (ex.: um comando local)."""
        self.lembrar_troca(
            [{"role": "user", "content": pergunta}, {"role": "assistant", "content": resposta}]
        )

    def lembrar_troca(self, mensagens: list[dict]) -> None:
        """Uma troca completa, como a IA a viu (com chamadas e resultados de ferramentas)."""
        guardadas = [_encurtar(m) for m in mensagens]
        with self._trava:
            self._expirar()
            self._trocas.append(guardadas)
            self._ultima_vez = self._relogio()

    def recentes(self) -> list[dict]:
        """As trocas no formato de mensagens da IA, das mais antigas às mais novas."""
        with self._trava:
            self._expirar()
            return [mensagem for troca in self._trocas for mensagem in troca]

    def esquecer(self) -> None:
        with self._trava:
            self._trocas.clear()

    def _expirar(self) -> None:
        if self._relogio() - self._ultima_vez > self._esquecer_apos:
            self._trocas.clear()


def _encurtar(mensagem: dict) -> dict:
    if mensagem.get("role") != "tool":
        return mensagem
    conteudo = mensagem.get("content") or ""
    if len(conteudo) <= MAXIMO_DE_LETRAS_DE_FERRAMENTA:
        return mensagem
    return {**mensagem, "content": conteudo[:MAXIMO_DE_LETRAS_DE_FERRAMENTA] + "..."}
