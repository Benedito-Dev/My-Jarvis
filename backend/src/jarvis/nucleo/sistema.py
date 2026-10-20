"""Abrir apps e sites: o único lugar que sabe como cada sistema faz isso.

Mesma ideia do `motor_voz.py`: funções puras montam o comando (texto → lista
de argumentos), com a plataforma passada por parâmetro. Assim os testes valem
para os três sistemas, rodando em qualquer máquina.

Segurança: o nome do app e o endereço vêm da IA. Nenhum comando passa por um
shell montado com texto livre, e os nomes são conferidos antes.
"""

import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from urllib.parse import urlparse

# Letras (com acento), números, espaço e . - + _ : o bastante para "Visual Studio Code".
NOME_DE_APP = re.compile(r"[\w .+\-]{1,60}")


class NaoConsigoAbrirError(RuntimeError):
    """O app não existe, o endereço é inválido ou o sistema recusou."""


def normalizar_endereco(endereco: str) -> str:
    """'youtube.com' vira 'https://youtube.com'. Só aceita http(s) com um domínio."""
    endereco = endereco.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", endereco, re.IGNORECASE):
        endereco = "https://" + endereco
    partes = urlparse(endereco)
    if partes.scheme not in ("http", "https") or "." not in partes.netloc or " " in endereco:
        raise NaoConsigoAbrirError(f"Endereço inválido: {endereco!r}.")
    return endereco


def comando_abrir_site(endereco: str, plataforma: str = sys.platform) -> list[str]:
    url = normalizar_endereco(endereco)
    if plataforma == "darwin":
        return ["open", url]
    if plataforma == "win32":
        # Sem o `cmd /c start`: o cmd quebraria URLs com "&" na busca.
        return ["rundll32", "url.dll,FileProtocolHandler", url]
    return ["xdg-open", url]


def comando_abrir_app(
    nome: str,
    plataforma: str = sys.platform,
    existe: Callable[[str], str | None] = shutil.which,
) -> list[str]:
    nome = nome.strip()
    if not NOME_DE_APP.fullmatch(nome):
        raise NaoConsigoAbrirError(f"Nome de app inválido: {nome!r}.")
    if plataforma == "darwin":
        return ["open", "-a", nome]
    if plataforma == "win32":
        return ["cmd", "/c", "start", "", nome]
    # Linux: o app é um programa no PATH ("Spotify" → spotify, "VS Code" → vs-code).
    for candidato in (nome.lower(), nome.lower().replace(" ", "-"), nome.lower().replace(" ", "")):
        caminho = existe(candidato)
        if caminho:
            return [caminho]
    raise NaoConsigoAbrirError(f"Não achei o app {nome!r} nesta máquina.")


def abrir(
    comando: list[str], rodar: Callable[..., subprocess.CompletedProcess] = subprocess.run
) -> None:
    """Roda o comando de abrir. No Mac, `open -a` com app inexistente sai com erro."""
    try:
        resultado = rodar(comando, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as erro:
        raise NaoConsigoAbrirError(f"O sistema não abriu ({erro}).") from erro
    if resultado.returncode != 0:
        raise NaoConsigoAbrirError("O sistema não encontrou o que abrir.")
