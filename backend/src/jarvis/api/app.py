"""Servidor FastAPI que o app (frontend) consulta."""

from importlib.metadata import version
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis.habilidades import HABILIDADES, Situacao
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.nucleo.config import NOME_ASSISTENTE

# Só a própria máquina acessa: o Jarvis não fica exposto na rede.
HOST = "127.0.0.1"
PORTA = 8765

# Endereços de onde o app pode chamar a API.
ORIGENS_PERMITIDAS = [
    "http://localhost:1420",  # app em desenvolvimento (npm run tauri dev)
    "tauri://localhost",  # app instalado (macOS)
]


class HabilidadeResposta(BaseModel):
    id: str
    nome: str
    descricao: str
    situacao: Situacao


class StatusResposta(BaseModel):
    nome: str
    versao: str
    habilidades: list[HabilidadeResposta]


class RostosResposta(BaseModel):
    cadastrados: list[str]


def criar_app(pasta_rostos: Path = banco_rostos.PASTA_ROSTOS) -> FastAPI:
    app = FastAPI(title="Jarvis", version=version("jarvis"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENS_PERMITIDAS,
        allow_methods=["GET"],
    )

    @app.get("/status")
    def status() -> StatusResposta:
        """Quem é o Jarvis e o que ele sabe fazer."""
        return StatusResposta(
            nome=NOME_ASSISTENTE,
            versao=version("jarvis"),
            habilidades=[
                HabilidadeResposta(id=h.id, nome=h.nome, descricao=h.descricao, situacao=h.situacao)
                for h in HABILIDADES
            ],
        )

    @app.get("/rostos")
    def rostos() -> RostosResposta:
        """Quem tem o rosto cadastrado (nomes prontos para exibir)."""
        nomes = banco_rostos.listar_nomes(pasta_rostos)
        return RostosResposta(cadastrados=[nome.capitalize() for nome in nomes])

    return app


def rodar() -> None:
    """Sobe o servidor e fica rodando até Ctrl+C."""
    uvicorn.run(criar_app(), host=HOST, port=PORTA)
