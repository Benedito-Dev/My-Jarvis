"""Configurações do Jarvis. Cada uma pode ser trocada por variável de ambiente."""

import os

# Como o assistente se chama. O app (frontend) exibe o que vier daqui.
# Exemplo: JARVIS_NOME="F.R.I.D.A.Y." uv run python -m jarvis servidor
NOME_ASSISTENTE = os.environ.get("JARVIS_NOME", "J.A.R.V.I.S.")
