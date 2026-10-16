"""Caminhos de pastas usados pelo Jarvis."""

from pathlib import Path

# caminhos.py → nucleo → jarvis → src → backend
PASTA_BACKEND = Path(__file__).resolve().parents[3]

# Dados pessoais (rostos cadastrados etc.). Fica fora do git (.gitignore).
PASTA_DADOS = PASTA_BACKEND / "dados"
