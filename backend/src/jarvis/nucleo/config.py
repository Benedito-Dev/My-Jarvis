"""Configurações do Jarvis. Cada uma pode ser trocada por variável de ambiente."""

import os
from pathlib import Path

# Como o assistente se chama. O app (frontend) exibe o que vier daqui.
# Exemplo: JARVIS_NOME="F.R.I.D.A.Y." uv run python -m jarvis servidor
NOME_ASSISTENTE = os.environ.get("JARVIS_NOME", "J.A.R.V.I.S.")


def carregar_segredos(arquivo: Path) -> None:
    """Lê `CHAVE=valor` de um .env para as variáveis de ambiente (ex.: a chave da IA).

    O que já estiver definido no ambiente vale mais que o arquivo. Linhas vazias
    e comentários (#) são ignorados. Sem o arquivo, não faz nada.
    """
    if not arquivo.exists():
        return
    for linha in arquivo.read_text().splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip("\"'"))
