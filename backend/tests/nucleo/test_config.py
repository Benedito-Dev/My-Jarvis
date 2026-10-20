import os

from jarvis.nucleo.config import carregar_segredos


def test_le_chaves_do_env(tmp_path, monkeypatch):
    # setenv + delenv: o monkeypatch apaga a variável de novo no fim do teste.
    monkeypatch.setenv("JARVIS_TESTE_CHAVE", "")
    monkeypatch.delenv("JARVIS_TESTE_CHAVE")
    arquivo = tmp_path / ".env"
    arquivo.write_text('# comentário\n\nJARVIS_TESTE_CHAVE="abc=123"\nlinha sem igual\n')

    carregar_segredos(arquivo)

    assert os.environ["JARVIS_TESTE_CHAVE"] == "abc=123"


def test_o_ambiente_vale_mais_que_o_arquivo(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_TESTE_CHAVE", "do-ambiente")
    arquivo = tmp_path / ".env"
    arquivo.write_text("JARVIS_TESTE_CHAVE=do-arquivo\n")

    carregar_segredos(arquivo)

    assert os.environ["JARVIS_TESTE_CHAVE"] == "do-ambiente"


def test_sem_arquivo_nao_faz_nada(tmp_path):
    carregar_segredos(tmp_path / "nao-existe.env")
