"""Cadastros de rosto em andamento, um por nome.

O app manda uma foto de cada vez e precisa saber quantas já entraram, então
alguém tem de lembrar disso entre as requisições. Esse alguém é aqui — e some
quando o cadastro termina ou é cancelado.
"""

import threading
from collections.abc import Callable
from pathlib import Path

import numpy as np

from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.cadastro import Cadastro, ResultadoAmostra

CriarCadastro = Callable[[str], Cadastro]


class Cadastros:
    """Os cadastros em andamento. Seguro para várias requisições ao mesmo tempo."""

    def __init__(
        self,
        pasta_rostos: Path = banco_rostos.PASTA_ROSTOS,
        criar: CriarCadastro | None = None,
    ) -> None:
        self._criar = criar or (lambda nome: Cadastro(nome, pasta_rostos))
        self._trava = threading.Lock()
        self._em_andamento: dict[str, Cadastro] = {}

    def adicionar_amostra(self, nome: str, quadro_bgr: np.ndarray) -> ResultadoAmostra:
        """Usa o quadro como amostra do cadastro de `nome`, começando um se preciso."""
        with self._trava:
            cadastro = self._em_andamento.get(nome.lower())
            if cadastro is None:
                # Criar valida o nome: um nome ruim falha antes de pedir fotos.
                cadastro = self._criar(nome)
                self._em_andamento[nome.lower()] = cadastro

            resultado = cadastro.adicionar(quadro_bgr)
            if cadastro.concluido:
                del self._em_andamento[nome.lower()]
            return resultado

    def cancelar(self, nome: str) -> bool:
        """Joga fora um cadastro pela metade. Retorna se havia algum."""
        with self._trava:
            return self._em_andamento.pop(nome.lower(), None) is not None
