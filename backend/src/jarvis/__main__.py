"""Ponto de entrada.

uv run python -m jarvis                        # tela de bloqueio: desbloqueia pelo rosto
uv run python -m jarvis cadastrar --nome Ana   # cadastra o rosto da Ana
uv run python -m jarvis ver                    # só mostra a câmera com os rostos marcados
"""

import argparse
import sys

from jarvis.habilidades import desbloqueio_facial
from jarvis.habilidades.desbloqueio_facial.banco_rostos import NomeInvalidoError
from jarvis.habilidades.desbloqueio_facial.camera import CameraIndisponivelError
from jarvis.habilidades.desbloqueio_facial.fluxo import NenhumRostoCadastradoError


def saudacao() -> str:
    return "Olá, eu sou o Jarvis"


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="jarvis")
    comandos = parser.add_subparsers(dest="comando")
    cadastro = comandos.add_parser("cadastrar", help="cadastra o rosto de uma pessoa")
    cadastro.add_argument("--nome", help="nome da pessoa (sem espaços)")
    comandos.add_parser("ver", help="mostra a câmera com os rostos marcados")
    return parser.parse_args()


def main() -> None:
    argumentos = _argumentos()
    print(saudacao())
    try:
        if argumentos.comando == "cadastrar":
            _cadastrar(argumentos.nome or input("Qual é o seu nome? ").strip())
        elif argumentos.comando == "ver":
            print("Abrindo a câmera... (aperte q ou ESC para sair)")
            desbloqueio_facial.executar()
        else:
            _desbloquear()
    except (CameraIndisponivelError, NomeInvalidoError, NenhumRostoCadastradoError) as erro:
        print(f"❌ {erro}", file=sys.stderr)
        sys.exit(1)
    print("Até logo!")


def _cadastrar(nome: str) -> None:
    print(f"Cadastrando o rosto de {nome}. Olhe para a câmera e aperte ESPAÇO.")
    caminho = desbloqueio_facial.cadastrar(nome)
    if caminho is None:
        print("Cadastro cancelado.")
    else:
        print(f"✅ Rosto de {nome} cadastrado em {caminho}")


def _desbloquear() -> None:
    print("🔒 Jarvis bloqueado. Olhe para a câmera... (q ou ESC para sair)")
    nome = desbloqueio_facial.desbloquear()
    if nome is None:
        print("Continua bloqueado.")
    else:
        print(f"🔓 Bem-vindo, {nome.capitalize()}!")


if __name__ == "__main__":
    main()
