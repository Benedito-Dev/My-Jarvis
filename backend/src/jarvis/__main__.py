"""Ponto de entrada: `uv run python -m jarvis`."""


def saudacao() -> str:
    return "Olá, eu sou o Jarvis"


def main() -> None:
    print(saudacao())


if __name__ == "__main__":
    main()
