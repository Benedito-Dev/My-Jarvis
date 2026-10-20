"""Servidor FastAPI que o app (frontend) consulta."""

import json
import queue
import threading
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from jarvis.api.cadastros import Cadastros
from jarvis.api.sessao import (
    CredenciaisPinInvalidasError,
    PinTemporariamenteBloqueadoError,
    Sessao,
    modelos,
)
from jarvis.habilidades import HABILIDADES, Situacao
from jarvis.habilidades.conversa import comandos, ferramentas, gravacoes
from jarvis.habilidades.conversa.cerebro import MODELO as MODELO_IA
from jarvis.habilidades.conversa.cerebro import (
    Cerebro,
    CerebroIndisponivelError,
    Frase,
    criar_cerebro,
)
from jarvis.habilidades.conversa.comandos import as_horas
from jarvis.habilidades.conversa.gravacoes import TipoDeAudioInvalidoError
from jarvis.habilidades.conversa.memoria import Memoria
from jarvis.habilidades.conversa.transcricao import TranscricaoIndisponivelError, Transcritor
from jarvis.habilidades.desbloqueio_facial import banco_rostos
from jarvis.habilidades.desbloqueio_facial.banco_rostos import NomeInvalidoError
from jarvis.habilidades.desbloqueio_facial.cadastro import EstadoCadastro
from jarvis.habilidades.desbloqueio_facial.desbloqueio import (
    EstadoDesbloqueio,
    NenhumRostoCadastradoError,
)
from jarvis.habilidades.lembretes.agenda import Agenda, Lembrete
from jarvis.habilidades.notas.caderno import Caderno
from jarvis.nucleo.acesso_pin import (
    AcessoPin,
    IdentificadorEmUsoError,
    IdentificadorInvalidoError,
    PinInvalidoError,
)
from jarvis.nucleo.caminhos import PASTA_BACKEND, PASTA_DADOS
from jarvis.nucleo.config import NOME_ASSISTENTE, carregar_segredos
from jarvis.nucleo.transmissao import Transmissao

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


class TextoRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=500)


class LembreteResposta(BaseModel):
    id: int
    texto: str
    quando: str  # ISO 8601, no fuso de São Paulo


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


def _em_fluxo(eventos: Iterator[str]) -> StreamingResponse:
    # Gerador comum (não async): o Starlette o roda numa thread, então as esperas
    # pela IA e pela voz não travam o servidor.
    return StreamingResponse(eventos, media_type="application/x-ndjson")


def _linha(**campos) -> str:
    """Uma linha do fluxo de eventos da conversa (NDJSON)."""
    return json.dumps(campos, ensure_ascii=False) + "\n"


def _lembrete(lembrete: Lembrete) -> "LembreteResposta":
    return LembreteResposta(
        id=lembrete.id, texto=lembrete.texto, quando=lembrete.quando.isoformat()
    )


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


# De quanto em quanto tempo vem um ponto do envelope da voz (voz_piper.envelope).
PASSO_DO_ENVELOPE_MS = 40

# Onde os lembretes ficam salvos entre um reinício e outro (fora do git).
ARQUIVO_LEMBRETES = PASTA_DADOS / "lembretes.json"

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
    agenda: Agenda | None = None,
    memoria: Memoria | None = None,
    caderno: Caderno | None = None,
) -> FastAPI:
    """Monta a API. Sem `cerebro`, perguntas livres recebem "Ainda não sei fazer isso"."""
    sessao = sessao or Sessao(pasta_rostos)
    memoria = memoria or Memoria()
    # Na hora do lembrete, o Jarvis fala, esteja bloqueado ou não (como um alarme).
    agenda = agenda or Agenda(avisar=lambda lem: sessao.falar(f"Lembrete: {lem.texto}."))
    # As "mãos" que a IA pode usar. Nova ferramenta = nova linha aqui.
    caderno = caderno or Caderno()
    maos = [
        ferramentas.lembrete(agenda),
        ferramentas.listar_lembretes(agenda),
        ferramentas.pesquisar_web(),
        ferramentas.clima(),
        ferramentas.abrir_site(),
        ferramentas.abrir_app(),
        ferramentas.anotar(caderno),
        ferramentas.ler_notas(caderno),
        ferramentas.calcular(),
    ]

    # Cada fala que começa a tocar vira um evento para o app (núcleo pulsando com
    # a voz de verdade). Inclui "Bem-vindo" e lembretes, não só as respostas.
    transmissao = Transmissao()
    sessao.observar_voz(
        lambda frase, envelope: transmissao.publicar(
            {"tipo": "fala", "frase": frase, "envelope": envelope, "passo_ms": PASSO_DO_ENVELOPE_MS}
        )
    )

    def trancar() -> None:
        """Bloqueia e esquece a conversa: a próxima pessoa não herda o contexto."""
        sessao.bloquear()
        memoria.esquecer()

        # Gerador comum (não async): o Starlette o roda numa thread, então as
        # esperas pela IA e pela voz não travam o servidor.

    def fluxo_da_conversa(texto: str, arquivo: str | None) -> Iterator[str]:
        """Os eventos de uma conversa (voz ou texto): ouvido, trechos, fim."""
        yield _linha(tipo="ouvido", texto=texto, arquivo=arquivo)
        resposta = comandos.responder(texto)
        if resposta is None:
            yield _linha(tipo="fim", acao=None)
            return

        # Não é um comando conhecido: pergunta à IA. Só com a sessão aberta, para
        # ninguém gastar o crédito (nem ler respostas) com o Jarvis bloqueado.
        usuario = sessao.usuario
        if not resposta.entendeu and cerebro is not None and usuario is not None:
            yield from _responder_com_a_ia(texto, usuario)
            yield _linha(tipo="fim", acao=None)
            return

        sessao.falar(resposta.fala)
        yield _linha(tipo="trecho", texto=resposta.fala)
        if resposta.acao == "bloquear":
            trancar()
        else:
            memoria.lembrar(texto, resposta.fala)
        yield _linha(tipo="fim", acao=resposta.acao)

    def _responder_com_a_ia(texto: str, usuario: str) -> Iterator[str]:
        sessao.calar()  # resposta nova: corta o que ele ainda estivesse falando
        falou = False
        try:
            for evento in cerebro.responder_em_fluxo(
                texto, usuario.capitalize(), historico=memoria.recentes(), ferramentas=maos
            ):
                if isinstance(evento, Frase):
                    sessao.falar_em_sequencia(evento.texto)
                    falou = True
                    yield _linha(tipo="trecho", texto=evento.texto)
                else:
                    memoria.lembrar_troca(evento.resposta.troca)  # com as ferramentas
        except CerebroIndisponivelError as erro:
            print(erro, flush=True)
            sessao.falar_em_sequencia(SEM_CEREBRO)
            yield _linha(tipo="trecho", texto=SEM_CEREBRO)
            return
        if not falou:
            sessao.falar_em_sequencia(comandos.NAO_SEI)
            yield _linha(tipo="trecho", texto=comandos.NAO_SEI)

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
        trancar()
        return SessaoResposta(usuario=None)

    @app.get("/voz/eventos")
    def eventos_da_voz() -> StreamingResponse:
        """Canal aberto (NDJSON): um evento a cada fala que começa, com o envelope do
        volume. A cada 15 s sem fala, um "pulso", para perceber quando o app sai."""

        def eventos() -> Iterator[str]:
            fila = transmissao.assinar()
            try:
                yield _linha(tipo="pulso")
                while True:
                    try:
                        yield _linha(**fila.get(timeout=15))
                    except queue.Empty:
                        yield _linha(tipo="pulso")
            finally:
                transmissao.cancelar(fila)

        return _em_fluxo(eventos())

    @app.get("/lembretes")
    def lembretes() -> list[LembreteResposta]:
        """Os lembretes que ainda vão tocar. Com o Jarvis bloqueado, nenhum aparece."""
        if sessao.usuario is None:
            return []
        return [_lembrete(lem) for lem in agenda.pendentes()]

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
    async def guardar_gravacao(request: Request) -> StreamingResponse:
        """Recebe o áudio gravado no app, guarda em dados/gravacoes/ e responde EM FLUXO.

        Uma linha JSON por evento (NDJSON), enviada assim que acontece:
        - {"tipo": "ouvido", "texto", "arquivo"}: o que foi dito (logo após transcrever);
        - {"tipo": "trecho", "texto"}: um pedaço da resposta, que já está sendo falado;
        - {"tipo": "fim", "acao"}: acabou ("bloquear" se for o caso).
        Assim o app mostra "Você disse..." e o Jarvis começa a falar antes de a IA
        terminar a resposta inteira.
        """
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

        return _em_fluxo(fluxo_da_conversa(texto, arquivo=caminho.name))

    @app.post("/conversa/texto")
    def conversar_por_texto(entrada: TextoRequest) -> StreamingResponse:
        """Igual à conversa por voz, para quando não dá para falar: o texto
        digitado entra direto, sem transcrição. Mesmo fluxo NDJSON."""
        return _em_fluxo(fluxo_da_conversa(entrada.texto.strip(), arquivo=None))

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
    estado = f"ligado ({MODELO_IA})" if cerebro else "desligado (sem chave)"
    print(f"Cérebro de IA: {estado}", flush=True)  # flush: aparece já, mesmo em segundo plano
    # Já deixa os modelos carregados: o primeiro desbloqueio não espera 2 s e a
    # primeira fala não espera o Whisper (~3 s, ou o download no primeiro uso).
    threading.Thread(target=modelos, daemon=True).start()
    threading.Thread(target=TRANSCRITOR.carregar, daemon=True).start()
    # E a voz: "Bem-vindo", "Aproxime seu rosto"... já geradas antes de precisar.
    sessao = Sessao()
    threading.Thread(target=sessao.preparar_voz, daemon=True).start()
    # Lembretes salvos em disco: voltam ao reiniciar, e os que venceram com o
    # Jarvis desligado são avisados assim que ele liga.
    agenda = Agenda(
        avisar=lambda lem: sessao.falar(f"Lembrete: {lem.texto}."), arquivo=ARQUIVO_LEMBRETES
    )
    atrasados = agenda.restaurar(avisar_atrasado=lambda _lembrete: None)
    if atrasados:
        sessao.falar(aviso_de_atrasados(atrasados))
    uvicorn.run(criar_app(sessao=sessao, cerebro=cerebro, agenda=agenda), host=HOST, port=PORTA)


def aviso_de_atrasados(atrasados: list[Lembrete]) -> str:
    """Uma frase só para todos (falas seguidas se cortariam): "Enquanto eu estava desligado..."."""
    itens = "; ".join(f"{as_horas(lem.quando)}, {lem.texto}" for lem in atrasados)
    if len(atrasados) == 1:
        return f"Enquanto eu estava desligado, venceu 1 lembrete: {itens}."
    return f"Enquanto eu estava desligado, venceram {len(atrasados)} lembretes: {itens}."
