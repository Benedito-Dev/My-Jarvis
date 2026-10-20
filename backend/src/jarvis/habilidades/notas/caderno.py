"""Persistência: guarda e lê as notas do dono num JSON em dados/. Não decide nada."""

import json
import threading
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from jarvis.habilidades.conversa.comandos import FUSO
from jarvis.nucleo.caminhos import PASTA_DADOS

ARQUIVO_NOTAS = PASTA_DADOS / "notas.json"
MAXIMO_DE_LETRAS = 500


class NotaInvalidaError(ValueError):
    """Nota vazia ou grande demais."""


@dataclass(frozen=True)
class Nota:
    id: int
    texto: str
    criada: str  # ISO 8601, fuso de São Paulo


class Caderno:
    def __init__(
        self,
        arquivo: Path = ARQUIVO_NOTAS,
        relogio: Callable[[], datetime] = lambda: datetime.now(FUSO),
    ) -> None:
        self._arquivo = arquivo
        self._relogio = relogio
        self._trava = threading.Lock()

    def anotar(self, texto: str) -> Nota:
        texto = texto.strip()
        if not texto:
            raise NotaInvalidaError("A nota está vazia.")
        if len(texto) > MAXIMO_DE_LETRAS:
            raise NotaInvalidaError(f"A nota passa de {MAXIMO_DE_LETRAS} letras.")
        with self._trava:
            notas = self._ler()
            nota = Nota(
                id=max((n.id for n in notas), default=0) + 1,
                texto=texto,
                criada=self._relogio().isoformat(timespec="seconds"),
            )
            self._gravar([*notas, nota])
        return nota

    def listar(self) -> list[Nota]:
        with self._trava:
            return self._ler()

    def _ler(self) -> list[Nota]:
        if not self._arquivo.exists():
            return []
        return [Nota(**item) for item in json.loads(self._arquivo.read_text())]

    def _gravar(self, notas: list[Nota]) -> None:
        self._arquivo.parent.mkdir(parents=True, exist_ok=True)
        temporario = self._arquivo.with_suffix(".tmp")
        temporario.write_text(json.dumps([asdict(n) for n in notas], ensure_ascii=False, indent=2))
        temporario.replace(self._arquivo)  # nunca deixa o arquivo pela metade
