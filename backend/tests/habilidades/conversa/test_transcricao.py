from jarvis.habilidades.conversa.transcricao import Transcritor, juntar_trechos


def test_junta_os_trechos_numa_frase():
    assert juntar_trechos([" Jarvis,", " que horas são?"]) == "Jarvis, que horas são?"


def test_ignora_trechos_vazios():
    assert juntar_trechos(["  ", " oi ", ""]) == "oi"


def test_nao_carrega_o_modelo_so_por_existir(tmp_path):
    # Criar o Transcritor tem que ser de graça: o Whisper só carrega no primeiro uso.
    transcritor = Transcritor(pasta=tmp_path)

    assert transcritor._modelo is None
    assert list(tmp_path.iterdir()) == []


def test_audio_quebrado_vira_texto_vazio(tmp_path):
    # Um toque rápido no ESPAÇO gera um webm de 5 bytes: antes, isso derrubava a rota.
    class ModeloQueNaoLe:
        def transcribe(self, *_a, **_k):
            raise ValueError("Invalid data found when processing input")

    transcritor = Transcritor(pasta=tmp_path)
    transcritor._modelo = ModeloQueNaoLe()
    quebrado = tmp_path / "toque.webm"
    quebrado.write_bytes(b"\x1a\x45\xdf\xa3\x00")

    assert transcritor.transcrever(quebrado) == ""
