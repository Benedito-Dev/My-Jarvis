"""Servidor FastAPI que o app (frontend) consulta."""

from importlib.metadata import version

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis.habilidades import HABILIDADES

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


class StatusResposta(BaseModel):
    nome: str
    versao: str
    habilidades: list[HabilidadeResposta]


def criar_app() -> FastAPI:
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
            nome="J.A.R.V.I.S.",
            versao=version("jarvis"),
            habilidades=[
                HabilidadeResposta(id=h.id, nome=h.nome, descricao=h.descricao) for h in HABILIDADES
            ],
        )

    return app


def rodar() -> None:
    """Sobe o servidor e fica rodando até Ctrl+C."""
    uvicorn.run(criar_app(), host=HOST, port=PORTA)
