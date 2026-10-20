"""Servidor FastAPI que o app (frontend) consulta."""

import threading
from importlib.metadata import version
from pathlib import Path

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from jarvis.api.cadastros import Cadastros
from jarvis.api.sessao import (
    CredenciaisPinInvalidasError,
    PinTemporariamenteBloqueadoError,
    Sessao,
    modelos,
)
from jarvis.habilidades import HABILIDADES, Situacao
from jarvis.habilidades.conversa import comandos, gravacoes
from jarvis.habilidades.conversa.cerebro import MODELO as MODELO_IA
from jarvis.habilidades.conversa.cerebro import Cerebro, CerebroIndisponivelError, criar_cerebro
from jarvis.habilidades.conversa.gravacoes import TipoDeAudioInvalidoError
from jarvis.habilidades.conversa.transcricao import TranscricaoIndisponivelError, Transcritor
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.banco_rostos import NomeInvalidoError
from jarvis.habilidades.desbloqueio_facial.cadastro import EstadoCadastro
from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    EstadoDesbloqueio,
    NenhumRostoCadastradoError,
)
from jarvis.nucleo.acesso_pin import (
    AcessoPin,
    IdentificadorEmUsoError,
    IdentificadorInvalidoError,
    PinInvalidoError,
)
from jarvis.nucleo.caminhos import PASTA_BACKEND
from jarvis.nucleo.config import NOME_ASSISTENTE, carregar_segredos

# Só a própria máquina acessa: o Jarvis não fica exposto na rede.
HOST = "127.0.0.1"
PORTA = 8765

# Endereços de onde o app pode chamar a API. A origem do webview muda conforme
# o sistema, então os três precisam estar aqui (decisão 0012).
ORIGENS_PERMITIDAS = [
    "http://localhost:1420",  # app em desenvolvimento (npm run tauri dev), nos três
    "tauri://localhost",  # app instalado no macOS e no Linux
    "http://tauri.localhost",  # app instalado no Windows (lá o webview não usa tauri://)
]

# Um quadro JPEG de 640x360 tem uns 30-60 KB. Bem acima disso é engano ou abuso.
TAMANHO_MAXIMO_QUADRO = 2 * 1024 * 1024

# Um minuto de voz em webm/opus dá uns 500 KB. 10 MB cobre falas bem longas.
TAMANHO_MAXIMO_AUDIO = 10 * 1024 * 1024


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


class LoginPinRequest(BaseModel):
    identificador: str
    pin: str


class ConfigurarPinRequest(BaseModel):
    identificador: str
    pin: str


class GravacaoResposta(BaseModel):
    arquivo: str
    bytes: int
    # O que foi dito. Vazio quando não deu para entender nada.
    texto: str
    # O que o Jarvis respondeu (e falou em voz alta). None se não houve fala.
    resposta: str | None = None
    # O que ele fez além de falar: hoje só "bloquear".
    acao: str | None = None


class AmostraResposta(BaseModel):
    estado: EstadoCadastro
    capturadas: int
    necessarias: int
    rostos: list["RetanguloResposta"]


class PontoResposta(BaseModel):
    nome: str
    x: int
    y: int


class RetanguloResposta(BaseModel):
    topo: int
    direita: int
    base: int
    esquerda: int
    # Olhos, nariz e cantos da boca: o app desenha o scanner em cima deles.
    pontos: list[PontoResposta] = []


class AvaliacaoResposta(BaseModel):
    estado: EstadoDesbloqueio
    progresso: float
    usuario: str | None
    rostos: list[RetanguloResposta]


def _exibir(nome: str | None) -> str | None:
    return nome.capitalize() if nome else None


async def _imagem_do_corpo(request: Request) -> "np.ndarray":
    """Lê o corpo da requisição como imagem, ou recusa com o motivo."""
    dados = await request.body()
    if len(dados) > TAMANHO_MAXIMO_QUADRO:
        raise HTTPException(413, "Quadro grande demais.")
    quadro = cv2.imdecode(np.frombuffer(dados, np.uint8), cv2.IMREAD_COLOR)
    if quadro is None:
        raise HTTPException(400, "O corpo precisa ser uma imagem JPEG ou PNG.")
    return quadro


def _retangulos(rostos) -> list["RetanguloResposta"]:
    return [
        RetanguloResposta(
            topo=r.topo,
            direita=r.direita,
            base=r.base,
            esquerda=r.esquerda,
            pontos=[PontoResposta(nome=p.nome, x=p.x, y=p.y) for p in r.pontos],
        )
        for r in rostos
    ]


# Quando a IA não responde (sem internet, sem crédito...).
SEM_CEREBRO = "Não consegui pensar nisso agora. Tente de novo em instantes."

# Um só Whisper para o servidor inteiro: carregar leva segundos e ocupa ~500 MB.
TRANSCRITOR = Transcritor()


def criar_app(
    pasta_rostos: Path = banco_rostos.PASTA_ROSTOS,
    sessao: Sessao | None = None,
    acesso_pin: AcessoPin | None = None,
    pasta_gravacoes: Path = gravacoes.PASTA_GRAVACOES,
    transcritor: Transcritor | None = None,
    cadastros: Cadastros | None = None,
    cerebro: Cerebro | None = None,
) -> FastAPI:
    """Monta a API. Sem `cerebro`, perguntas livres recebem "Ainda não sei fazer isso"."""
    sessao = sessao or Sessao(pasta_rostos)
    acesso_pin = acesso_pin or AcessoPin()
    cadastros = cadastros or Cadastros(pasta_rostos)
    transcritor = transcritor or TRANSCRITOR
    app = FastAPI(title="Jarvis", version=version("jarvis"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ORIGENS_PERMITIDAS,
        allow_methods=["GET", "POST", "DELETE"],
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
        """Quem tem o rosto cadastrado, somente depois do desbloqueio."""
        if sessao.usuario is None:
            raise HTTPException(401, "Desbloqueie o Jarvis para consultar essa informação.")
        nomes = banco_rostos.listar_nomes(pasta_rostos)
        return RostosResposta(cadastrados=[nome.capitalize() for nome in nomes])

    @app.get("/sessao")
    def ver_sessao() -> SessaoResposta:
        """Bloqueado (usuario = null) ou desbloqueado por quem."""
        return SessaoResposta(usuario=_exibir(sessao.usuario))

    @app.post("/sessao/bloquear")
    def bloquear() -> SessaoResposta:
        """Tranca o Jarvis de novo (botão Bloquear do app)."""
        sessao.bloquear()
        return SessaoResposta(usuario=None)

    @app.post("/sessao/pin")
    def desbloquear_por_pin(entrada: LoginPinRequest) -> SessaoResposta:
        """Desbloqueia pelo identificador digitado e PIN, sem enumerar perfis."""
        try:
            usuario = sessao.desbloquear_por_pin(
                entrada.identificador,
                entrada.pin,
                acesso_pin,
            )
        except PinTemporariamenteBloqueadoError as erro:
            raise HTTPException(
                429,
                str(erro),
                headers={"Retry-After": str(erro.restante_s)},
            ) from erro
        except CredenciaisPinInvalidasError as erro:
            raise HTTPException(401, "Identificador ou PIN inválido.") from erro
        return SessaoResposta(usuario=_exibir(usuario))

    @app.post("/sessao/pin/configurar")
    def configurar_pin(entrada: ConfigurarPinRequest) -> dict[str, bool]:
        """Cadastra ou troca o acesso alternativo do usuário já autenticado."""
        usuario = sessao.usuario
        if usuario is None:
            raise HTTPException(401, "Desbloqueie o Jarvis antes de configurar o PIN.")
        try:
            acesso_pin.configurar(entrada.identificador, usuario, entrada.pin)
        except (IdentificadorInvalidoError, PinInvalidoError) as erro:
            raise HTTPException(422, str(erro)) from erro
        except IdentificadorEmUsoError as erro:
            raise HTTPException(409, str(erro)) from erro
        return {"configurado": True}

    @app.post("/cadastro/{nome}/amostra")
    async def cadastrar_amostra(nome: str, request: Request) -> AmostraResposta:
        """Recebe uma foto do app e a usa como amostra do rosto de `nome`."""
        quadro = await _imagem_do_corpo(request)
        try:
            # Reconhecer é trabalho pesado de CPU: roda fora do laço do servidor.
            resultado = await run_in_threadpool(cadastros.adicionar_amostra, nome, quadro)
        except NomeInvalidoError as erro:
            raise HTTPException(422, str(erro)) from erro

        return AmostraResposta(
            estado=resultado.estado,
            capturadas=resultado.capturadas,
            necessarias=resultado.necessarias,
            rostos=_retangulos(resultado.rostos),
        )

    @app.delete("/cadastro/{nome}")
    def cancelar_cadastro(nome: str) -> dict[str, bool]:
        """Joga fora um cadastro pela metade (o app abandonou a tela)."""
        return {"havia": cadastros.cancelar(nome)}

    @app.post("/conversa/gravacao")
    async def guardar_gravacao(request: Request) -> GravacaoResposta:
        """Recebe o áudio gravado no app, guarda em dados/gravacoes/ e diz o que foi dito."""
        audio = await request.body()
        if not audio:
            raise HTTPException(400, "A gravação chegou vazia.")
        if len(audio) > TAMANHO_MAXIMO_AUDIO:
            raise HTTPException(413, "Gravação grande demais.")

        tipo = request.headers.get("content-type", "audio/webm")
        try:
            caminho = await run_in_threadpool(gravacoes.salvar, audio, tipo, pasta_gravacoes)
        except TipoDeAudioInvalidoError as erro:
            raise HTTPException(415, str(erro)) from erro

        try:
            # Transcrever é trabalho pesado de CPU: roda fora do laço principal.
            texto = await run_in_threadpool(transcritor.transcrever, caminho)
        except TranscricaoIndisponivelError as erro:
            raise HTTPException(503, str(erro)) from erro

        resposta = comandos.responder(texto)
        if resposta is None:
            return GravacaoResposta(arquivo=caminho.name, bytes=len(audio), texto=texto)

        # Não é um comando conhecido: pergunta à IA. Só com a sessão aberta, para
        # ninguém gastar o crédito (nem ler respostas) com o Jarvis bloqueado.
        usuario = sessao.usuario
        if not resposta.entendeu and cerebro is not None and usuario is not None:
            try:
                fala = await run_in_threadpool(cerebro.responder, texto, usuario.capitalize())
                resposta = comandos.Resposta(fala=fala or comandos.NAO_SEI)
            except CerebroIndisponivelError as erro:
                print(erro)
                resposta = comandos.Resposta(fala=SEM_CEREBRO, entendeu=False)

        sessao.falar(resposta.fala)
        if resposta.acao == "bloquear":
            sessao.bloquear()
        return GravacaoResposta(
            arquivo=caminho.name,
            bytes=len(audio),
            texto=texto,
            resposta=resposta.fala,
            acao=resposta.acao,
        )

    @app.post("/desbloqueio/quadro")
    async def avaliar_quadro(request: Request) -> AvaliacaoResposta:
        """Recebe uma foto JPEG da câmera do app e responde em que pé está o desbloqueio."""
        quadro = await _imagem_do_corpo(request)
        try:
            # Reconhecer é trabalho pesado de CPU: roda fora do laço principal do servidor.
            avaliacao = await run_in_threadpool(sessao.avaliar_quadro, quadro)
        except NenhumRostoCadastradoError as erro:
            raise HTTPException(409, str(erro)) from erro

        return AvaliacaoResposta(
            estado=avaliacao.estado,
            progresso=avaliacao.progresso,
            usuario=_exibir(avaliacao.usuario),
            rostos=_retangulos(avaliacao.rostos),
        )

    return app


def rodar() -> None:
    """Sobe o servidor e fica rodando até Ctrl+C."""
    # Segredos (a chave da IA) vêm de backend/.env, que não vai para o git.
    carregar_segredos(PASTA_BACKEND / ".env")
    cerebro = criar_cerebro()
    print(f"Cérebro de IA: {'ligado (' + MODELO_IA + ')' if cerebro else 'desligado (sem chave)'}")
    # Já deixa os modelos carregados: o primeiro desbloqueio não espera 2 s e a
    # primeira fala não espera o Whisper (~3 s, ou o download no primeiro uso).
    threading.Thread(target=modelos, daemon=True).start()
    threading.Thread(target=TRANSCRITOR.carregar, daemon=True).start()
    # E a voz: "Bem-vindo", "Aproxime seu rosto"... já geradas antes de precisar.
    sessao = Sessao()
    threading.Thread(target=sessao.preparar_voz, daemon=True).start()
    uvicorn.run(criar_app(sessao=sessao, cerebro=cerebro), host=HOST, port=PORTA)
