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
