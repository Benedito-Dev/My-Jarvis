"""Persistência: guarda os áudios gravados pelo app. Não decide nada."""

from datetime import datetime
from pathlib import Path

from jarvis.nucleo.caminhos import PASTA_DADOS

PASTA_GRAVACOES = PASTA_DADOS / "gravacoes"

# O MediaRecorder do app entrega webm no Chromium/WebKitGTK. Guardamos o que
# vier, mas só com extensão conhecida, para nunca escrever um nome arbitrário.
EXTENSOES = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
}
EXTENSAO_PADRAO = ".webm"


class TipoDeAudioInvalidoError(ValueError):
    """O app mandou um formato de áudio que não sabemos guardar."""


def extensao_de(tipo_conteudo: str) -> str:
    """Extensão para um Content-Type. Ignora parâmetros como '; codecs=opus'."""
    tipo = tipo_conteudo.split(";")[0].strip().lower()
    if not tipo:
        return EXTENSAO_PADRAO
    if tipo not in EXTENSOES:
        raise TipoDeAudioInvalidoError(
            f"Não sei guardar áudio do tipo {tipo!r}. Conhecidos: {', '.join(sorted(EXTENSOES))}."
        )
    return EXTENSOES[tipo]


def salvar(
    audio: bytes,
    tipo_conteudo: str = "audio/webm",
    pasta: Path = PASTA_GRAVACOES,
    agora: datetime | None = None,
) -> Path:
    """Salva o áudio com a data e hora no nome, e devolve onde ficou."""
    momento = agora or datetime.now()
    caminho = pasta / f"{momento:%Y-%m-%d_%H-%M-%S}{extensao_de(tipo_conteudo)}"
    pasta.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(audio)
    return caminho
