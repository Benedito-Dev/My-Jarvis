"""Persistência: salva e carrega as assinaturas dos rostos cadastrados."""

import re
from pathlib import Path

import numpy as np

from jarvis.nucleo.caminhos import PASTA_DADOS

PASTA_ROSTOS = PASTA_DADOS / "rostos"


class NomeInvalidoError(ValueError):
    """O nome não pode virar um nome de arquivo seguro."""


def _caminho(nome: str, pasta: Path) -> Path:
    if not re.fullmatch(r"[\w-]+", nome):
        raise NomeInvalidoError(
            f"Nome inválido: {nome!r}. Use só letras, números, - ou _ (sem espaços)."
        )
    return pasta / f"{nome.lower()}.npy"


def salvar(nome: str, assinaturas: list[np.ndarray], pasta: Path = PASTA_ROSTOS) -> Path:
    """Salva as assinaturas de uma pessoa (substitui um cadastro anterior)."""
    caminho = _caminho(nome, pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    np.save(caminho, np.stack(assinaturas))
    return caminho


def carregar(nome: str, pasta: Path = PASTA_ROSTOS) -> np.ndarray | None:
    """Retorna as assinaturas (uma por linha) ou None se a pessoa não está cadastrada."""
    caminho = _caminho(nome, pasta)
    if not caminho.exists():
        return None
    return np.load(caminho)


def carregar_todos(pasta: Path = PASTA_ROSTOS) -> dict[str, np.ndarray]:
    """Retorna {nome: assinaturas} de todas as pessoas cadastradas."""
    if not pasta.exists():
        return {}
    return {caminho.stem: np.load(caminho) for caminho in sorted(pasta.glob("*.npy"))}


def listar_nomes(pasta: Path = PASTA_ROSTOS) -> list[str]:
    """Nomes das pessoas cadastradas, sem carregar as assinaturas."""
    if not pasta.exists():
        return []
    return [caminho.stem for caminho in sorted(pasta.glob("*.npy"))]
