"""Lógica: encontra rostos e gera suas assinaturas. Não sabe que existe câmera ou tela."""

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from jarvis.nucleo.arquivos import baixar_se_necessario

PASTA_MODELOS = Path(__file__).parent / "modelos"

# --- Detecção (onde está o rosto?) ---------------------------------------------

# Modelo YuNet do OpenCV Zoo (licença MIT): detector de rostos leve e rápido.
CAMINHO_MODELO = PASTA_MODELOS / "face_detection_yunet_2023mar.onnx"

# Detectar na imagem inteira (1280x720) é desperdício. Reduzimos para esta
# largura, detectamos e convertemos as posições de volta para o tamanho original.
LARGURA_DETECCAO = 320

# De 0 a 1: quão confiante o modelo precisa estar para dizer "isto é um rosto".
CONFIANCA_MINIMA = 0.8

# --- Reconhecimento (de quem é o rosto?) ---------------------------------------

# Modelo SFace do OpenCV Zoo (licença Apache 2.0). Tem 37 MB, por isso não fica
# no git: é baixado no primeiro uso e conferido pelo hash.
URL_MODELO_SFACE = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_recognition_sface/face_recognition_sface_2021dec.onnx"
)
SHA256_MODELO_SFACE = "0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79"
CAMINHO_MODELO_SFACE = PASTA_MODELOS / "face_recognition_sface_2021dec.onnx"


# Ordem dos 5 pontos que o YuNet devolve, depois do retângulo.
NOMES_DOS_PONTOS = ("olho_direito", "olho_esquerdo", "nariz", "boca_direita", "boca_esquerda")


@dataclass(frozen=True)
class Ponto:
    """Um ponto do rosto, em pixels da imagem original."""

    nome: str
    x: int
    y: int


@dataclass(frozen=True)
class Rosto:
    """Retângulo de um rosto, em pixels da imagem original."""

    topo: int
    direita: int
    base: int
    esquerda: int
    # Linha completa do YuNet já na escala original: retângulo, 5 pontos do
    # rosto (olhos, nariz, boca) e confiança. O SFace usa os pontos para alinhar.
    deteccao: np.ndarray | None = field(default=None, compare=False, repr=False)

    @property
    def pontos(self) -> list[Ponto]:
        """Olhos, nariz e cantos da boca. Vazio se o rosto não veio do detector.

        O SFace já usava esses pontos para alinhar o rosto; expô-los deixa o app
        desenhar em cima do rosto em vez de só contorná-lo.
        """
        if self.deteccao is None:
            return []
        return [
            Ponto(
                nome, round(float(self.deteccao[4 + i * 2])), round(float(self.deteccao[5 + i * 2]))
            )
            for i, nome in enumerate(NOMES_DOS_PONTOS)
        ]


class DetectorDeRostos:
    """Carrega o modelo uma vez e detecta rostos em quantos quadros precisar."""

    def __init__(
        self,
        caminho_modelo: Path = CAMINHO_MODELO,
        largura_deteccao: int = LARGURA_DETECCAO,
        confianca_minima: float = CONFIANCA_MINIMA,
    ) -> None:
        self._largura = largura_deteccao
        # O tamanho de entrada é ajustado a cada quadro em `detectar`.
        self._modelo = cv2.FaceDetectorYN.create(
            str(caminho_modelo), "", (largura_deteccao, largura_deteccao), confianca_minima
        )

    def detectar(self, quadro_bgr: np.ndarray) -> list[Rosto]:
        """Retorna os rostos encontrados no quadro (formato BGR, o padrão do OpenCV)."""
        altura, largura = quadro_bgr.shape[:2]
        escala = self._largura / largura
        tamanho_reduzido = (self._largura, round(altura * escala))
        pequeno = cv2.resize(quadro_bgr, tamanho_reduzido)

        self._modelo.setInputSize(tamanho_reduzido)
        _, deteccoes = self._modelo.detect(pequeno)
        if deteccoes is None:
            return []

        rostos = []
        for linha in deteccoes:
            # Os 14 primeiros valores são coordenadas; o último é a confiança.
            original = linha.copy()
            original[:14] /= escala
            x, y, w, h = original[:4]
            rostos.append(
                Rosto(
                    topo=round(y),
                    direita=round(x + w),
                    base=round(y + h),
                    esquerda=round(x),
                    deteccao=original,
                )
            )
        return rostos


class ExtratorDeAssinaturas:
    """Transforma um rosto numa assinatura: 128 números que o identificam."""

    def __init__(self, caminho_modelo: Path | None = None) -> None:
        if caminho_modelo is None:
            caminho_modelo = baixar_se_necessario(
                URL_MODELO_SFACE, CAMINHO_MODELO_SFACE, SHA256_MODELO_SFACE
            )
        self._modelo = cv2.FaceRecognizerSF.create(str(caminho_modelo), "")

    def extrair(self, quadro_bgr: np.ndarray, rosto: Rosto) -> np.ndarray:
        """Retorna a assinatura (vetor de 128 floats) do rosto no quadro."""
        if rosto.deteccao is None:
            raise ValueError("O rosto precisa vir do DetectorDeRostos (com os pontos do rosto).")
        alinhado = self._modelo.alignCrop(quadro_bgr, rosto.deteccao)
        return self._modelo.feature(alinhado).flatten().copy()


# --- Identificação (é alguém cadastrado?) --------------------------------------

# Similaridade de cosseno mínima para considerar "mesma pessoa". É o valor
# recomendado pelos autores do SFace (vai de -1 a 1; quanto maior, mais parecido).
LIMIAR_MESMA_PESSOA = 0.363

# Rostos muito pequenos (longe da câmera) geram assinaturas ruins.
# Exigimos que o rosto ocupe pelo menos esta fração da largura da imagem.
LARGURA_MINIMA_ROSTO = 0.15

# Quantos quadros seguidos precisam reconhecer a mesma pessoa para desbloquear.
# Evita que um único quadro "sortudo" abra o Jarvis.
QUADROS_PARA_CONFIRMAR = 5


@dataclass(frozen=True)
class Identificacao:
    """Resultado da comparação: quem é (ou None) e quão parecido estava."""

    nome: str | None
    similaridade: float


def similaridade(assinatura: np.ndarray, outra: np.ndarray) -> float:
    """Similaridade de cosseno entre duas assinaturas (1 = idênticas)."""
    return float(np.dot(assinatura, outra) / (np.linalg.norm(assinatura) * np.linalg.norm(outra)))


def identificar(
    assinatura: np.ndarray,
    cadastrados: dict[str, np.ndarray],
    limiar: float = LIMIAR_MESMA_PESSOA,
) -> Identificacao:
    """Compara a assinatura com todas as amostras de todos os cadastrados.

    Fica com a pessoa da amostra mais parecida, se passar do limiar.
    """
    melhor_nome, melhor = None, -1.0
    for nome, amostras in cadastrados.items():
        for amostra in amostras:
            valor = similaridade(assinatura, amostra)
            if valor > melhor:
                melhor_nome, melhor = nome, valor
    return Identificacao(nome=melhor_nome if melhor >= limiar else None, similaridade=melhor)


def esta_perto(rosto: Rosto, largura_quadro: int, minimo: float = LARGURA_MINIMA_ROSTO) -> bool:
    """O rosto está perto o suficiente da câmera para ser reconhecido?"""
    return (rosto.direita - rosto.esquerda) / largura_quadro >= minimo


class ConfirmadorDeDesbloqueio:
    """Só confirma quando a mesma pessoa é reconhecida em N quadros seguidos."""

    def __init__(self, quadros_necessarios: int = QUADROS_PARA_CONFIRMAR) -> None:
        self._necessarios = quadros_necessarios
        self._nome: str | None = None
        self._seguidos = 0

    def registrar(self, nome: str | None) -> str | None:
        """Registra quem foi visto neste quadro. Retorna o nome quando confirmar."""
        if nome is None or nome != self._nome:
            self._nome = nome
            self._seguidos = 0 if nome is None else 1
        else:
            self._seguidos += 1
        return self._nome if self._seguidos >= self._necessarios else None

    @property
    def progresso(self) -> float:
        """De 0 a 1: quanto falta para confirmar."""
        return min(self._seguidos / self._necessarios, 1.0)
