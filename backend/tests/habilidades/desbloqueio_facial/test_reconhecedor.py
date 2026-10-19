import numpy as np
import pytest

from jarvis.habilidades.desbloqueio_facial.reconhecedor import (
    CAMINHO_MODELO_SFACE,
    ConfirmadorDeDesbloqueio,
    DetectorDeRostos,
    ExtratorDeAssinaturas,
    Rosto,
    esta_perto,
    identificar,
    similaridade,
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


# --- Identificação ---------------------------------------------------------------


def vetor(*valores: float) -> np.ndarray:
    return np.array(valores, dtype=np.float32)


def test_similaridade_de_cosseno():
    assert similaridade(vetor(1, 0), vetor(2, 0)) == pytest.approx(1.0)  # mesma direção
    assert similaridade(vetor(1, 0), vetor(0, 1)) == pytest.approx(0.0)  # perpendiculares
    assert similaridade(vetor(1, 0), vetor(-1, 0)) == pytest.approx(-1.0)  # opostas


def test_identifica_a_pessoa_mais_parecida():
    cadastrados = {
        "ana": np.stack([vetor(1, 0, 0), vetor(0.9, 0.1, 0)]),
        "bia": np.stack([vetor(0, 1, 0)]),
    }

    resultado = identificar(vetor(0.1, 1, 0), cadastrados)

    assert resultado.nome == "bia"
    assert resultado.similaridade > 0.9


def test_desconhecido_abaixo_do_limiar():
    cadastrados = {"ana": np.stack([vetor(1, 0, 0)])}

    resultado = identificar(vetor(0, 0, 1), cadastrados)

    assert resultado.nome is None
    assert resultado.similaridade == pytest.approx(0.0)


def test_rosto_perto_ou_longe():
    largo = Rosto(topo=0, direita=300, base=300, esquerda=0)  # 300 de 1280 = 23%
    estreito = Rosto(topo=0, direita=100, base=100, esquerda=0)  # 100 de 1280 = 8%

    assert esta_perto(largo, largura_quadro=1280)
    assert not esta_perto(estreito, largura_quadro=1280)


def test_confirma_so_depois_de_n_quadros_seguidos():
    confirmador = ConfirmadorDeDesbloqueio(quadros_necessarios=3, segundos_necessarios=0)

    assert confirmador.registrar("ana") is None
    assert confirmador.registrar("ana") is None
    assert confirmador.progresso == pytest.approx(2 / 3)
    assert confirmador.registrar("ana") == "ana"


def test_quadro_sem_reconhecimento_zera_a_contagem():
    confirmador = ConfirmadorDeDesbloqueio(quadros_necessarios=2, segundos_necessarios=0)

    confirmador.registrar("ana")
    confirmador.registrar(None)

    assert confirmador.progresso == 0
    assert confirmador.registrar("ana") is None


def test_trocar_de_pessoa_recomeca_a_contagem():
    confirmador = ConfirmadorDeDesbloqueio(quadros_necessarios=2, segundos_necessarios=0)

    confirmador.registrar("ana")

    assert confirmador.registrar("bia") is None
    assert confirmador.registrar("bia") == "bia"


def test_quadros_rapidos_nao_confirmam_antes_do_tempo():
    agora = [0.0]
    confirmador = ConfirmadorDeDesbloqueio(
        quadros_necessarios=2, segundos_necessarios=1.0, relogio=lambda: agora[0]
    )

    confirmador.registrar("ana")
    agora[0] = 0.25
    assert confirmador.registrar("ana") is None  # quadros bastam, tempo não
    assert confirmador.progresso == pytest.approx(0.25)

    agora[0] = 1.0
    assert confirmador.registrar("ana") == "ana"


# --- Pontos do rosto (olhos, nariz, boca) -----------------------------------------


def test_rosto_sem_deteccao_nao_tem_pontos():
    from jarvis.habilidades.desbloqueio_facial.reconhecedor import Rosto

    assert Rosto(topo=1, direita=2, base=3, esquerda=0).pontos == []


def test_pontos_saem_da_linha_do_yunet():
    import numpy as np

    from jarvis.habilidades.desbloqueio_facial.reconhecedor import NOMES_DOS_PONTOS, Rosto

    # x,y,w,h seguidos dos 5 pontos (x,y) e da confiança.
    linha = np.array(
        [10, 20, 100, 120, 40, 50, 80, 50, 60, 70, 45, 90, 75, 90, 0.9], dtype=np.float32
    )
    rosto = Rosto(topo=20, direita=110, base=140, esquerda=10, deteccao=linha)

    pontos = rosto.pontos

    assert [p.nome for p in pontos] == list(NOMES_DOS_PONTOS)
    assert [(p.x, p.y) for p in pontos] == [(40, 50), (80, 50), (60, 70), (45, 90), (75, 90)]
