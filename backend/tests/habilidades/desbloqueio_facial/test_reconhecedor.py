import numpy as np
import pytest

from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    CAMINHO_MODELO_SFACE,
    DetectorDeRostos,
    ExtratorDeAssinaturas,
    Rosto,
)


class ModeloFalso:
    """Imita o cv2.FaceDetectorYN para testar a conversão de posições."""

    def __init__(self, deteccoes: np.ndarray | None) -> None:
        self.deteccoes = deteccoes
        self.tamanho_entrada = None
        self.formato_recebido = None

    def setInputSize(self, tamanho):  # noqa: N802 (nome da API do OpenCV)
        self.tamanho_entrada = tamanho

    def detect(self, imagem):
        self.formato_recebido = imagem.shape
        return 1, self.deteccoes


def test_modelo_real_carrega_e_imagem_sem_rosto_retorna_vazio():
    preta = np.zeros((720, 1280, 3), dtype=np.uint8)

    assert DetectorDeRostos().detectar(preta) == []


def test_posicoes_voltam_para_o_tamanho_original():
    detector = DetectorDeRostos(largura_deteccao=320)
    # Uma detecção: x=20, y=10, largura=40, altura=40 (+ pontos do rosto e confiança)
    modelo = ModeloFalso(np.array([[20, 10, 40, 40] + [0] * 10 + [0.99]], dtype=np.float32))
    detector._modelo = modelo
    quadro = np.zeros((720, 1280, 3), dtype=np.uint8)

    rostos = detector.detectar(quadro)

    assert modelo.formato_recebido == (180, 320, 3)  # detecção roda na imagem reduzida
    assert modelo.tamanho_entrada == (320, 180)
    assert rostos == [Rosto(topo=40, direita=240, base=200, esquerda=80)]
    # Pontos do rosto também voltam para a escala original; a confiança não muda.
    np.testing.assert_allclose(rostos[0].deteccao[:4], [80, 40, 160, 160])
    assert rostos[0].deteccao[14] == pytest.approx(0.99)


def test_sem_deteccao_retorna_lista_vazia():
    detector = DetectorDeRostos()
    detector._modelo = ModeloFalso(None)

    assert detector.detectar(np.zeros((720, 1280, 3), dtype=np.uint8)) == []


def test_extrair_exige_rosto_vindo_do_detector():
    extrator = ExtratorDeAssinaturas.__new__(ExtratorDeAssinaturas)  # sem carregar modelo

    with pytest.raises(ValueError, match="DetectorDeRostos"):
        extrator.extrair(np.zeros((10, 10, 3), dtype=np.uint8), Rosto(0, 1, 1, 0))


@pytest.mark.skipif(not CAMINHO_MODELO_SFACE.exists(), reason="modelo SFace ainda não baixado")
def test_assinatura_tem_128_numeros():
    extrator = ExtratorDeAssinaturas(CAMINHO_MODELO_SFACE)
    quadro = np.full((720, 1280, 3), 128, dtype=np.uint8)
    deteccao = np.array(
        [500, 200, 200, 250, 560, 300, 640, 300, 600, 350, 570, 400, 630, 400, 0.99],
        dtype=np.float32,
    )
    rosto = Rosto(topo=200, direita=700, base=450, esquerda=500, deteccao=deteccao)

    assinatura = extrator.extrair(quadro, rosto)

    assert assinatura.shape == (128,)
