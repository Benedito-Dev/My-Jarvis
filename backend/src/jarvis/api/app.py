"""Servidor FastAPI que o app (frontend) consulta."""

from importlib.metadata import version
from pathlib import Path

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis.api.sessao import Sessao
from jarvis.habilidades import HABILIDADES, Situacao
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    EstadoDesbloqueio,
    NenhumRostoCadastradoError,
)
from jarvis.nucleo.config import NOME_ASSISTENTE

# Só a própria máquina acessa: o Jarvis não fica exposto na rede.
HOST = "127.0.0.1"
PORTA = 8765

# Endereços de onde o app pode chamar a API.
ORIGENS_PERMITIDAS = [
    "http://localhost:1420",  # app em desenvolvimento (npm run tauri dev)
    "tauri://localhost",  # app instalado (macOS)
]

# Um quadro JPEG de 640x360 tem uns 30-60 KB. Bem acima disso é engano ou abuso.
TAMANHO_MAXIMO_QUADRO = 2 * 1024 * 1024


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


class SessaoResposta(BaseModel):
    usuario: str | None  # None = bloqueado


class RetanguloResposta(BaseModel):
    topo: int
    direita: int
    base: int
    esquerda: int


class AvaliacaoResposta(BaseModel):
    estado: EstadoDesbloqueio
    progresso: float
    usuario: str | None
    rostos: list[RetanguloResposta]


def _exibir(nome: str | None) -> str | None:
    return nome.capitalize() if nome else None


def criar_app(
    pasta_rostos: Path = banco_rostos.PASTA_ROSTOS, sessao: Sessao | None = None
) -> FastAPI:
    sessao = sessao or Sessao(pasta_rostos)
    app = FastAPI(title="Jarvis", version=version("jarvis"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENS_PERMITIDAS,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
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

    @app.get("/sessao")
    def ver_sessao() -> SessaoResposta:
        """Bloqueado (usuario = null) ou desbloqueado por quem."""
        return SessaoResposta(usuario=_exibir(sessao.usuario))

    @app.post("/desbloqueio/quadro")
    async def avaliar_quadro(request: Request) -> AvaliacaoResposta:
        """Recebe uma foto JPEG da câmera do app e responde em que pé está o desbloqueio."""
        dados = await request.body()
        if len(dados) > TAMANHO_MAXIMO_QUADRO:
            raise HTTPException(413, "Quadro grande demais.")
        quadro = cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)
        if quadro is None:
            raise HTTPException(400, "O corpo precisa ser uma imagem JPEG ou PNG.")

        try:
            # Reconhecer é trabalho pesado de CPU: roda fora do laço principal do servidor.
            avaliacao = await run_in_threadpool(sessao.avaliar_quadro, quadro)
        except NenhumRostoCadastradoError as erro:
            raise HTTPException(409, str(erro)) from erro

        return AvaliacaoResposta(
            estado=avaliacao.estado,
            progresso=avaliacao.progresso,
            usuario=_exibir(avaliacao.usuario),
            rostos=[
                RetanguloResposta(topo=r.topo, direita=r.direita, base=r.base, esquerda=r.esquerda)
                for r in avaliacao.rostos
            ],
        )

    return app


def rodar() -> None:
    """Sobe o servidor e fica rodando até Ctrl+C."""
    uvicorn.run(criar_app(), host=HOST, port=PORTA)
