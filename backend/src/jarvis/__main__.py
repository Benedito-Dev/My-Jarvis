"""Ponto de entrada do Jarvis."""

import argparse
import getpass
import sys

from jarvis.api import app as api
from jarvis.habilidades import desbloqueio_facial
from jarvis.habilidades.desbloqueio_facial.banco_rostos import NomeInvalidoError
from jarvis.habilidades.desbloqueio_facial.camera import CameraIndisponivelError
from jarvis.habilidades.desbloqueio_facial.desbloqueio import NenhumRostoCadastradoError
from jarvis.nucleo.acesso_pin import AcessoPin, IdentificadorEmUsoError, PinInvalidoError


def saudacao() -> str:
    return "Olá, eu sou o Jarvis"


def _argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="jarvis")
    comandos = parser.add_subparsers(dest="comando")
    cadastro = comandos.add_parser("cadastrar", help="cadastra o rosto de uma pessoa")
    cadastro.add_argument("--nome", help="nome da pessoa (sem espaços)")
    comandos.add_parser("ver", help="mostra a câmera com os rostos marcados")
    comandos.add_parser("servidor", help="sobe a API local para o app (frontend)")

    pin = comandos.add_parser("pin", help="gerencia o acesso alternativo por PIN")
    pin_comandos = pin.add_subparsers(dest="pin_comando", required=True)
    cadastrar_pin = pin_comandos.add_parser("cadastrar", help="cadastra ou troca um PIN")
    cadastrar_pin.add_argument("--usuario", required=True)
    cadastrar_pin.add_argument("--identificador", required=True)
    cadastrar_pin.add_argument(
        "--pin",
        help="PIN de 6 dígitos; sem ele, pergunta de forma oculta",
    )
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
        elif argumentos.comando == "servidor":
            print(f"Servidor em http://{api.HOST}:{api.PORTA} (Ctrl+C para parar)")
            api.rodar()
        elif argumentos.comando == "pin":
            _cadastrar_pin(argumentos)
        else:
            _desbloquear()
    except (CameraIndisponivelError, NomeInvalidoError, NenhumRostoCadastradoError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        sys.exit(1)
    print("Até logo!")


def _cadastrar(nome: str) -> None:
    print(f"Cadastrando o rosto de {nome}. Olhe para a câmera e aperte ESPAÇO.")
    caminho = desbloqueio_facial.cadastrar(nome)
    if caminho is None:
        print("Cadastro cancelado.")
    else:
        print(f"OK: Rosto de {nome} cadastrado em {caminho}")


def _desbloquear() -> None:
    print("🔒 Jarvis bloqueado. Olhe para a câmera... (q ou ESC para sair)")
    nome = desbloqueio_facial.desbloquear()
    if nome is None:
        print("Continua bloqueado.")
    else:
        print(f"🔓 Bem-vindo, {nome.capitalize()}!")


def _cadastrar_pin(argumentos: argparse.Namespace) -> None:
    pin = argumentos.pin or getpass.getpass("PIN de 6 dígitos: ")
    try:
        AcessoPin().configurar(argumentos.identificador, argumentos.usuario, pin)
    except (IdentificadorEmUsoError, PinInvalidoError, ValueError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        sys.exit(1)
    print(f"OK: Acesso alternativo configurado para {argumentos.identificador}.")


if __name__ == "__main__":
    main()
