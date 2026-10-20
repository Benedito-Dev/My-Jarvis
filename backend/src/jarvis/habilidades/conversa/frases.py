"""Lógica: corta o texto que a IA vai escrevendo em frases prontas para falar.

A IA manda a resposta aos pedacinhos (algumas letras por vez). Assim que uma
frase fecha (". ", "! ", "? "), ela já pode ir para a voz, enquanto a IA
escreve a próxima: o Jarvis começa a falar em vez de esperar o texto todo.
"""

import re

# Frase curta demais vira um soluço na fala ("Sim." "Claro."): espera juntar mais.
MINIMO_DE_LETRAS = 25
# Pontuação que fecha frase, seguida de espaço. Não corta "3.5" nem "Sr.Benedito".
_FIM_DE_FRASE = re.compile(r"[.!?…]+[\"')\]]*\s+")


def fatiar(acumulado: str) -> tuple[list[str], str]:
    """Separa as frases já completas do que ainda está chegando.

    Devolve (frases prontas, resto). Frases menores que o mínimo são juntadas
    à seguinte, para a voz não sair picada.
    """
    prontas: list[str] = []
    inicio = 0
    for fim in _FIM_DE_FRASE.finditer(acumulado):
        trecho = acumulado[inicio : fim.end()].strip()
        if len(trecho) >= MINIMO_DE_LETRAS:
            prontas.append(trecho)
            inicio = fim.end()
    return prontas, acumulado[inicio:]
