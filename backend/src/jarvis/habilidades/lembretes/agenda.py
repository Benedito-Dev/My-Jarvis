"""Lógica: guarda lembretes e dispara cada um na hora certa.

Não sabe falar: quem fala é a função `avisar`, passada por quem cria a agenda.
O relógio e o "agendador" também são passados, para os testes não esperarem.
Com `arquivo`, os pendentes ficam salvos em disco e voltam ao reiniciar
(`restaurar`); sem ele, vivem só na memória (como nos testes).
"""

import json
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from itertools import count
from pathlib import Path

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
    arquivo: Path | None = None
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
        self._agendar(lembrete, daqui_a_minutos * 60)
        return lembrete

    def restaurar(self, avisar_atrasado: Callable[[Lembrete], None]) -> list[Lembrete]:
        """Recarrega os lembretes salvos. Os futuros voltam a ser agendados; os que
        venceram com o Jarvis desligado vão para `avisar_atrasado`. Devolve os atrasados.
        """
        if self.arquivo is None or not self.arquivo.exists():
            return []
        salvos = [
            Lembrete(item["id"], item["texto"], datetime.fromisoformat(item["quando"]))
            for item in json.loads(self.arquivo.read_text())
        ]
        # Os ids continuam de onde pararam: um lembrete novo nunca repete o id de um salvo.
        self._ids = count(max((lem.id for lem in salvos), default=0) + 1)
        agora = self.relogio()
        atrasados = []
        for lembrete in salvos:
            falta = (lembrete.quando - agora).total_seconds()
            if falta > 0:
                self._agendar(lembrete, falta)
            else:
                atrasados.append(lembrete)
        self._salvar()  # o arquivo fica só com os que ainda vão tocar
        for lembrete in atrasados:
            avisar_atrasado(lembrete)
        return atrasados

    def _agendar(self, lembrete: Lembrete, segundos: float) -> None:
        temporizador = self.agendar(segundos, lambda: self._disparar(lembrete.id))
        with self._trava:
            self._pendentes[lembrete.id] = (lembrete, temporizador)
        self._salvar()

    def pendentes(self) -> list[Lembrete]:
        """Os lembretes que ainda vão tocar, do mais próximo ao mais distante."""
        with self._trava:
            return sorted((lem for lem, _ in self._pendentes.values()), key=lambda lem: lem.quando)

    def _disparar(self, id_: int) -> None:
        with self._trava:
            item = self._pendentes.pop(id_, None)
        if item is not None:
            self._salvar()
            self.avisar(item[0])

    def _salvar(self) -> None:
        """Grava os pendentes (se a agenda tiver arquivo). Nunca deixa o JSON pela metade."""
        if self.arquivo is None:
            return
        with self._trava:
            itens = [
                {"id": lem.id, "texto": lem.texto, "quando": lem.quando.isoformat()}
                for lem, _ in self._pendentes.values()
            ]
        self.arquivo.parent.mkdir(parents=True, exist_ok=True)
        temporario = self.arquivo.with_suffix(".tmp")
        temporario.write_text(json.dumps(itens, ensure_ascii=False, indent=2))
        temporario.replace(self.arquivo)
