"""Lógica: guarda lembretes e dispara cada um na hora certa.

Não sabe falar: quem fala é a função `avisar`, passada por quem cria a agenda.
O relógio e o "agendador" também são passados, para os testes não esperarem.
Os lembretes vivem na memória: reiniciar o servidor os perde (por enquanto).
"""

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import count

from jarvis.habilidades.conversa.comandos import FUSO

MAXIMO_DE_MINUTOS = 24 * 60  # até um dia; mais que isso pede uma agenda de verdade


class LembreteInvalidoError(ValueError):
    """Tempo fora do intervalo aceito ou texto vazio."""


@dataclass(frozen=True)
class Lembrete:
    id: int
    texto: str
    quando: datetime


class _Cancelavel:
    def cancel(self) -> None: ...


def _agendar_com_timer(segundos: float, acao: Callable[[], None]) -> _Cancelavel:
    timer = threading.Timer(segundos, acao)
    timer.daemon = True  # não segura o servidor aberto ao desligar
    timer.start()
    return timer


@dataclass
class Agenda:
    avisar: Callable[[Lembrete], None]
    agendar: Callable[[float, Callable[[], None]], _Cancelavel] = _agendar_com_timer
    relogio: Callable[[], datetime] = lambda: datetime.now(FUSO)
    _pendentes: dict[int, tuple[Lembrete, _Cancelavel]] = field(default_factory=dict)
    _ids: count = field(default_factory=lambda: count(1))
    _trava: threading.Lock = field(default_factory=threading.Lock)

    def criar(self, daqui_a_minutos: float, texto: str) -> Lembrete:
        texto = texto.strip()
        if not texto:
            raise LembreteInvalidoError("O lembrete precisa dizer o que lembrar.")
        if not 0 < daqui_a_minutos <= MAXIMO_DE_MINUTOS:
            raise LembreteInvalidoError(
                f"Só consigo lembrar entre agora e {MAXIMO_DE_MINUTOS // 60} horas."
            )
        lembrete = Lembrete(
            id=next(self._ids),
            texto=texto,
            quando=self.relogio() + timedelta(minutes=daqui_a_minutos),
        )
        temporizador = self.agendar(daqui_a_minutos * 60, lambda: self._disparar(lembrete.id))
        with self._trava:
            self._pendentes[lembrete.id] = (lembrete, temporizador)
        return lembrete

    def pendentes(self) -> list[Lembrete]:
        """Os lembretes que ainda vão tocar, do mais próximo ao mais distante."""
        with self._trava:
            return sorted((lem for lem, _ in self._pendentes.values()), key=lambda lem: lem.quando)

    def _disparar(self, id_: int) -> None:
        with self._trava:
            item = self._pendentes.pop(id_, None)
        if item is not None:
            self.avisar(item[0])
