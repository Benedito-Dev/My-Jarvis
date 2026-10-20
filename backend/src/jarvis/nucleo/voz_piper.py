"""A voz do Jarvis: Piper TTS com a voz "Faber" (pt-BR), igual nos três sistemas.

Gera o áudio de cada frase num .wav e guarda: a mesma frase não é gerada duas
vezes. Quem toca o arquivo é o comando do sistema (`motor_voz.py`), e quem
decide *quando* falar é o `Locutor` (`voz.py`). Ver decisão 0017.
"""

import hashlib
import threading
import wave
from collections.abc import Callable, Iterable
from pathlib import Path

from jarvis.nucleo.arquivos import baixar_se_necessario
from jarvis.nucleo.caminhos import PASTA_DADOS

PASTA_MODELOS = Path(__file__).parent / "modelos"
# Áudios já gerados. Fica em dados/ (fora do git) porque guarda frases ditas.
PASTA_CACHE = PASTA_DADOS / "voz"

_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium"
MODELO = PASTA_MODELOS / "pt_BR-faber-medium.onnx"
ARQUIVOS = {
    MODELO: (
        f"{_BASE}/pt_BR-faber-medium.onnx",
        "858555e3a064209c57088fe6bd70c4c3dc54d03eaa00c45d5ecaf43a33f95aa7",
    ),
    MODELO.with_suffix(".onnx.json"): (
        f"{_BASE}/pt_BR-faber-medium.onnx.json",
        "7e694de195ae3fc36dd732c445eb04fb49b649854893cb5506b978f0d50a1d6f",
    ),
}

# Quantos áudios o cache guarda. Frases como "São 14 horas e 54" (e, mais
# adiante, respostas da IA) quase nunca se repetem: sem limite, a pasta só cresce.
# ~500 x ~60 KB = ~30 MB no máximo.
MAXIMO_NO_CACHE = 500

# Escreve o áudio de `frase` em `destino` (.wav).
Sintetizador = Callable[[str, Path], None]


def nome_no_cache(frase: str) -> str:
    """Nome do .wav de uma frase: o mesmo texto sempre cai no mesmo arquivo."""
    return hashlib.sha256(frase.encode()).hexdigest()[:20] + ".wav"


def _sintetizador_piper() -> Sintetizador:
    """Baixa o modelo (só na primeira vez, ~63 MB) e carrega o Piper."""
    for destino, (url, sha256) in ARQUIVOS.items():
        baixar_se_necessario(url, destino, sha256)
    from piper import PiperVoice  # import pesado: só quando for falar

    voz = PiperVoice.load(str(MODELO))

    def sintetizar(frase: str, destino: Path) -> None:
        with wave.open(str(destino), "wb") as arquivo:
            voz.synthesize_wav(frase, arquivo)

    return sintetizar


class VozPiper:
    """Transforma frases em arquivos de áudio, com cache.

    Criar é de graça: o modelo só é baixado e carregado na primeira frase
    (ou em `preparar`, que o servidor chama ao subir).
    """

    def __init__(
        self,
        pasta_cache: Path = PASTA_CACHE,
        carregar: Callable[[], Sintetizador] = _sintetizador_piper,
        maximo_no_cache: int = MAXIMO_NO_CACHE,
    ) -> None:
        self._pasta = pasta_cache
        self._maximo = maximo_no_cache
        self._carregar = carregar
        self._sintetizar: Sintetizador | None = None
        self._trava = threading.Lock()

    def arquivo_da_frase(self, frase: str) -> Path:
        """O .wav com a frase falada. Gera só se ainda não estiver no cache."""
        destino = self._pasta / nome_no_cache(frase)
        with self._trava:
            if destino.exists():
                destino.touch()  # usada agora: fica entre as últimas a sair do cache
                return destino
            if self._sintetizar is None:
                self._sintetizar = self._carregar()
            self._pasta.mkdir(parents=True, exist_ok=True)
            # Gera ao lado e só então renomeia: nunca toca um .wav pela metade.
            parcial = destino.with_suffix(".parcial.wav")
            self._sintetizar(frase, parcial)
            parcial.replace(destino)
            self._limitar_cache()
        return destino

    def _limitar_cache(self) -> None:
        """Apaga os áudios usados há mais tempo quando o cache passa do limite."""
        audios = sorted(self._pasta.glob("*.wav"), key=lambda p: p.stat().st_mtime)
        for velho in audios[: max(0, len(audios) - self._maximo)]:
            velho.unlink(missing_ok=True)

    def preparar(self, frases: Iterable[str]) -> None:
        """Deixa estas frases prontas no cache, para saírem sem espera."""
        for frase in frases:
            self.arquivo_da_frase(frase)


# Volume "cheio" da voz Faber: um RMS de 0,35 vira nível 1. Medido: a fala fica
# entre 0,15 (p50) e 0,28 (p90), com picos de ~0,4.
RMS_DE_REFERENCIA = 0.35
PASSO_DO_ENVELOPE_S = 0.04


def envelope(arquivo: Path, passo_s: float = PASSO_DO_ENVELOPE_S) -> list[float]:
    """O volume da fala a cada `passo_s` segundos, de 0 a 1.

    É o que o app usa para o núcleo pulsar junto com a voz de verdade: o áudio
    toca no backend, e o app não o ouve.
    """
    import numpy as np  # já vem com o OpenCV; só aqui para não pesar o import

    with wave.open(str(arquivo)) as audio:
        taxa = audio.getframerate()
        amostras = np.frombuffer(audio.readframes(audio.getnframes()), dtype=np.int16)
    sinal = amostras.astype(np.float32) / 32768
    janela = max(1, int(taxa * passo_s))
    niveis = []
    for inicio in range(0, len(sinal), janela):
        pedaco = sinal[inicio : inicio + janela]
        rms = float(np.sqrt(np.mean(pedaco * pedaco)))
        niveis.append(round(min(1.0, rms / RMS_DE_REFERENCIA), 2))
    return niveis
