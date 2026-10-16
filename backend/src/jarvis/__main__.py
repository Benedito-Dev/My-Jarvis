"""Ponto de entrada: `uv run python -m jarvis`."""

import sys

from jarvis.habilidades import desbloqueio_facial
from jarvis.habilidades.desbloqueio_facial.camera import CameraIndisponivelError


def saudacao() -> str:
    return "Olá, eu sou o Jarvis"


def main() -> None:
    print(saudacao())
    print("Abrindo a câmera... (aperte q ou ESC para sair)")
    try:
        desbloqueio_facial.executar()
    except CameraIndisponivelError as erro:
        print(f"❌ {erro}", file=sys.stderr)
        sys.exit(1)
    print("Até logo!")


if __name__ == "__main__":
    main()
