from datetime import datetime

import pytest

from jarvis.habilidades.conversa import gravacoes
from jarvis.habilidades.conversa.gravacoes import TipoDeAudioInvalidoError

MOMENTO = datetime(2026, 10, 17, 9, 5, 3)


def test_salva_com_data_e_hora_no_nome(tmp_path):
    caminho = gravacoes.salvar(b"audio", "audio/webm", pasta=tmp_path, agora=MOMENTO)

    assert caminho.name == "2026-10-17_09-05-03.webm"
    assert caminho.read_bytes() == b"audio"


def test_cria_a_pasta_se_nao_existir(tmp_path):
    destino = tmp_path / "ainda-nao-existe"

    caminho = gravacoes.salvar(b"audio", pasta=destino, agora=MOMENTO)

    assert caminho.parent == destino


def test_extensao_ignora_os_codecs_do_navegador():
    # O MediaRecorder manda 'audio/webm;codecs=opus'.
    assert gravacoes.extensao_de("audio/webm;codecs=opus") == ".webm"
    assert gravacoes.extensao_de("AUDIO/OGG") == ".ogg"


def test_sem_tipo_assume_webm():
    assert gravacoes.extensao_de("") == ".webm"


def test_tipo_desconhecido_nao_vira_arquivo(tmp_path):
    with pytest.raises(TipoDeAudioInvalidoError):
        gravacoes.salvar(b"audio", "application/x-coisa-estranha", pasta=tmp_path)

    assert list(tmp_path.glob("*")) == []
