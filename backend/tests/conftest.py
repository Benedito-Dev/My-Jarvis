import pytest


@pytest.fixture(autouse=True)
def jarvis_mudo(monkeypatch):
    """Nenhum teste fala em voz alta nem baixa o modelo de voz (~63 MB)."""
    monkeypatch.setenv("JARVIS_MUDO", "1")
