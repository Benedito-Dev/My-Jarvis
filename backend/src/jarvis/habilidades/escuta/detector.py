"""Lógica: ouve o som do microfone, aos pedaços, e diz quando alguém chamou "Jarvis".

Duas partes:
- `Caracteristicas`: transforma o som em "características" de fala, com dois
  modelos genéricos do openWakeWord (espectrograma + embedding do Google,
  Apache 2.0). A cada 80 ms de som sai uma linha de 96 números.
- `Classificador`: uma rede pequena, treinada com a voz do dono (ver
  `ferramentas/treinar_escuta.py`), que olha as últimas 16 linhas (~1,3 s) e dá
  a chance de ter ouvido "Jarvis" agora.

O `Detector` junta as duas e decide: só dispara com duas notas altas seguidas e
depois espera um pouco, para um "Jarvis" não disparar várias vezes.
"""

from collections import deque
from collections.abc import Callable
from pathlib import Path

import numpy as np

from jarvis.nucleo.arquivos import baixar_se_necessario
from jarvis.nucleo.caminhos import PASTA_DADOS

TAXA = 16000  # o app manda o som em 16 kHz, mono, 16 bits
BLOCO = 1280  # 80 ms: o passo dos modelos do openWakeWord
CONTEXTO = 480  # o espectrograma de um bloco precisa de 30 ms do anterior
QUADROS_POR_EMBEDDING = 76  # ~0,8 s de espectrograma por linha de características
JANELA = 16  # quantas linhas o classificador olha de uma vez (~1,3 s)
LIMIAR = 0.7  # nos testes: 14 de 17 chamadas, ~3 alarmes falsos por hora de fala
ESPERA_DEPOIS_DE_DISPARAR_S = 2.0

PASTA_MODELOS = Path(__file__).parent / "modelos"
# O classificador é treinado com a voz do dono: fica em dados/, fora do git.
ARQUIVO_CLASSIFICADOR = PASTA_DADOS / "escuta" / "jarvis.npz"

_BASE = "https://github.com/dscripka/openWakeWord/releases/download/v0.5.1"
ESPECTROGRAMA = PASTA_MODELOS / "melspectrogram.onnx"
EMBEDDING = PASTA_MODELOS / "embedding_model.onnx"
ARQUIVOS = {
    ESPECTROGRAMA: (
        f"{_BASE}/melspectrogram.onnx",
        "ba2b0e0f8b7b875369a2c89cb13360ff53bac436f2895cced9f479fa65eb176f",
    ),
    EMBEDDING: (
        f"{_BASE}/embedding_model.onnx",
        "70d164290c1d095d1d4ee149bc5e00543250a7316b59f31d056cff7bd3075c1f",
    ),
}


class EscutaIndisponivelError(RuntimeError):
    """Falta o classificador treinado (ou os modelos não baixaram)."""


class Caracteristicas:
    """Som (int16, 16 kHz) → uma linha de 96 números a cada 80 ms, como no treino."""

    def __init__(self) -> None:
        for destino, (url, sha256) in ARQUIVOS.items():
            baixar_se_necessario(url, destino, sha256)
        import onnxruntime as ort  # import pesado: só quando for ouvir

        opcoes = ort.SessionOptions()
        opcoes.inter_op_num_threads = opcoes.intra_op_num_threads = 1
        provedor = ["CPUExecutionProvider"]
        self._espectrograma = ort.InferenceSession(str(ESPECTROGRAMA), opcoes, providers=provedor)
        self._embedding = ort.InferenceSession(str(EMBEDDING), opcoes, providers=provedor)
        self.recomecar()

    def recomecar(self) -> None:
        self._som = np.zeros(CONTEXTO, np.int16)
        # Começa "cheio" como no openWakeWord, para a primeira linha sair logo.
        self._quadros = np.ones((QUADROS_POR_EMBEDDING, 32), np.float32)

    def __call__(self, bloco: np.ndarray) -> np.ndarray:
        """As características do bloco de 80 ms (1280 amostras)."""
        som = np.concatenate([self._som[-CONTEXTO:], bloco])
        self._som = som
        espectro = self._espectrograma.run(None, {"input": som[None].astype(np.float32)})[0]
        quadros = np.squeeze(espectro) / 10 + 2  # o mesmo ajuste do openWakeWord
        self._quadros = np.vstack([self._quadros, quadros])[-QUADROS_POR_EMBEDDING:]
        entrada = self._quadros[None, :, :, None].astype(np.float32)
        return np.squeeze(self._embedding.run(None, {"input_1": entrada})[0])


class Classificador:
    """A rede pequena (uma camada escondida), lida do .npz que o treino gera."""

    def __init__(self, arquivo: Path = ARQUIVO_CLASSIFICADOR) -> None:
        if not arquivo.exists():
            raise EscutaIndisponivelError(
                "A escuta ainda não foi treinada com a sua voz (falta dados/escuta/jarvis.npz)."
            )
        pesos = np.load(arquivo)
        self._w1, self._b1 = pesos["w1"], pesos["b1"]
        self._w2, self._b2 = pesos["w2"], pesos["b2"]

    def __call__(self, janela: np.ndarray) -> float:
        escondida = np.maximum(0, janela.reshape(-1) @ self._w1 + self._b1)
        return float(1 / (1 + np.exp(-(escondida @ self._w2 + self._b2)[0])))


class Detector:
    """Recebe o som aos pedaços (qualquer tamanho) e avisa quando ouviu "Jarvis"."""

    def __init__(
        self,
        caracteristicas: Callable[[np.ndarray], np.ndarray],
        classificador: Callable[[np.ndarray], float],
        limiar: float = LIMIAR,
    ) -> None:
        self._caracteristicas = caracteristicas
        self._classificador = classificador
        self._limiar = limiar
        self._sobra = np.zeros(0, np.int16)
        self._linhas: deque[np.ndarray] = deque(maxlen=JANELA)
        self._nota_anterior = 0.0
        self._blocos_de_espera = 0

    def ouvir(self, som: np.ndarray) -> bool:
        """True se "Jarvis" acabou de ser dito neste pedaço de som."""
        som = np.concatenate([self._sobra, som.astype(np.int16)])
        inteiros = len(som) // BLOCO * BLOCO
        self._sobra = som[inteiros:]
        ouviu = False
        for inicio in range(0, inteiros, BLOCO):
            ouviu = self._bloco(som[inicio : inicio + BLOCO]) or ouviu
        return ouviu

    def _bloco(self, bloco: np.ndarray) -> bool:
        self._linhas.append(self._caracteristicas(bloco))
        if self._blocos_de_espera > 0:
            self._blocos_de_espera -= 1
            return False
        if len(self._linhas) < JANELA:
            return False
        nota = self._classificador(np.array(self._linhas))
        # Duas notas altas seguidas: um pico isolado (um estalo, uma sílaba) não conta.
        disparou = min(nota, self._nota_anterior) >= self._limiar
        self._nota_anterior = nota
        if disparou:
            self._nota_anterior = 0.0
            self._blocos_de_espera = int(ESPERA_DEPOIS_DE_DISPARAR_S * TAXA / BLOCO)
        return disparou


def criar_detector() -> Detector:
    """O detector de verdade. Levanta EscutaIndisponivelError sem o treino da voz."""
    classificador = Classificador()
    return Detector(Caracteristicas(), classificador)
