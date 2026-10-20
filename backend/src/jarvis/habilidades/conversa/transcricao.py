"""Lógica: transforma a voz gravada em texto, com o Whisper rodando local.

Nada sai da máquina: o modelo é baixado uma vez para `modelos/` (fora do git)
e roda na CPU. O `faster-whisper` lê webm, ogg e m4a direto, os formatos que o
app grava em cada sistema.
"""

import os
import threading
from collections.abc import Iterable
from pathlib import Path

# "small": acerta frases como "que horas são agora?", que o "base" trocava por
# "que oraçam agora". ~460 MB, baixados no primeiro uso. Numa máquina fraca,
# `JARVIS_WHISPER=base` troca por um modelo 3x menor e mais rápido.
MODELO = os.environ.get("JARVIS_WHISPER", "small")
PASTA_MODELOS = Path(__file__).parent / "modelos"

# Palavras que o Jarvis espera ouvir. Sem esta dica, um "bloquear" dito sozinho
# saía "Bocchiar", "Burkia", "Bocinha"; com ela, 7 de 8 gravações reais acertaram,
# sem fazer o Whisper "ouvir bloquear" em frases que não tinham a palavra.
PALAVRAS_ESPERADAS = "Jarvis bloquear horas dia"


class TranscricaoIndisponivelError(RuntimeError):
    """O modelo não pôde ser carregado (ex.: sem internet no primeiro uso)."""


def juntar_trechos(trechos: Iterable[str]) -> str:
    """Junta os trechos que o Whisper devolve numa frase só, sem espaços sobrando."""
    return " ".join(texto.strip() for texto in trechos if texto.strip())


class Transcritor:
    """Carrega o Whisper na primeira vez que precisar e reaproveita depois."""

    def __init__(self, modelo: str = MODELO, pasta: Path = PASTA_MODELOS) -> None:
        self._nome = modelo
        self._pasta = pasta
        self._modelo = None
        self._trava = threading.Lock()

    def carregar(self) -> None:
        """Deixa o modelo pronto. Pode ser chamado antes, para o primeiro uso não esperar."""
        with self._trava:
            if self._modelo is not None:
                return
            from faster_whisper import WhisperModel  # import pesado: só quando usar

            try:
                self._modelo = WhisperModel(
                    self._nome, device="cpu", compute_type="int8", download_root=str(self._pasta)
                )
            except Exception as erro:
                raise TranscricaoIndisponivelError(
                    f"Não consegui carregar o modelo de transcrição ({erro})."
                ) from erro

    def transcrever(self, audio: Path) -> str:
        """O que foi dito no arquivo de áudio. Texto vazio se não entendeu nada."""
        self.carregar()
        try:
            return self._transcrever(audio)
        except Exception as erro:
            # Um toque rápido no ESPAÇO gera um áudio quebrado (ex.: 5 bytes), e
            # o leitor de áudio levanta erro. Para quem fala, é só "não entendi".
            print(f"Não consegui ler o áudio {audio.name} ({erro}).", flush=True)
            return ""

    def _transcrever(self, audio: Path) -> str:
        trechos, _info = self._modelo.transcribe(
            str(audio),
            language="pt",
            hotwords=PALAVRAS_ESPERADAS,
            beam_size=5,
            # Sem "tentar de novo mais criativo": com repetições na fala, isso
            # fazia uma frase de 5 s levar 11 s para sair.
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,  # corta o silêncio antes e depois da fala
        )
        return juntar_trechos(trecho.text for trecho in trechos)
