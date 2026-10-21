import pytest


@pytest.fixture(autouse=True)
def jarvis_mudo(monkeypatch):
    """Nenhum teste fala em voz alta nem baixa o modelo de voz (~63 MB)."""
    monkeypatch.setenv("JARVIS_MUDO", "1")


@pytest.fixture(autouse=True)
def sem_chave_de_ia(monkeypatch):
    """Nenhum teste chama a IA de verdade (nem gasta crédito)."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


@pytest.fixture(autouse=True)
def sem_configuracao_pessoal(monkeypatch):
    """A cidade e o feed de notícias do dono não mudam o resultado dos testes."""
    for nome in ("JARVIS_CIDADE", "JARVIS_NOTICIAS_LOCAL", "JARVIS_NOTICIAS_RSS"):
        monkeypatch.delenv(nome, raising=False)
