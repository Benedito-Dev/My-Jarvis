"""Lógica: resolve uma expressão aritmética com segurança, sem `eval`.

Lê a expressão como árvore do Python e só aceita números, + - * / // % ** e
parênteses. Qualquer outra coisa (nomes, chamadas, atributos) é recusada:
assim um texto vindo da IA nunca vira código rodando na máquina.
"""

import ast
import operator

OPERACOES = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
SINAIS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
MAIOR_EXPOENTE = 100  # 10 ** 10**9 travaria o servidor


class ContaInvalidaError(ValueError):
    """A expressão não é uma conta que sabemos (ou podemos) resolver."""


def calcular(expressao: str) -> float | int:
    # A IA às vezes escreve como se fala: "17% de 3480", "3,5 x 2".
    texto = expressao.replace(",", ".").replace("x", "*").replace("×", "*").replace("÷", "/")
    try:
        arvore = ast.parse(texto, mode="eval")
    except SyntaxError as erro:
        raise ContaInvalidaError(f"Não entendi a conta {expressao!r}.") from erro
    try:
        return _resolver(arvore.body)
    except ZeroDivisionError as erro:
        raise ContaInvalidaError("Divisão por zero.") from erro


def _resolver(no: ast.AST) -> float | int:
    if isinstance(no, ast.Constant) and type(no.value) in (int, float):
        return no.value
    if isinstance(no, ast.UnaryOp) and type(no.op) in SINAIS:
        return SINAIS[type(no.op)](_resolver(no.operand))
    if isinstance(no, ast.BinOp) and type(no.op) in OPERACOES:
        esquerda, direita = _resolver(no.left), _resolver(no.right)
        if isinstance(no.op, ast.Pow) and abs(direita) > MAIOR_EXPOENTE:
            raise ContaInvalidaError("Expoente grande demais.")
        return OPERACOES[type(no.op)](esquerda, direita)
    raise ContaInvalidaError("Só sei fazer contas com números e + - * / % **.")


def formatar(numero: float | int) -> str:
    """Sem ".0" sobrando e com no máximo 6 casas: 4.0 vira "4", 1/3 vira "0.333333"."""
    if isinstance(numero, float) and numero.is_integer():
        numero = int(numero)
    if isinstance(numero, int):
        return str(numero)
    return f"{numero:.6f}".rstrip("0").rstrip(".")
