"""Credenciais do acesso alternativo do Jarvis.

O identificador aponta para uma conta; o PIN prova que a pessoa conhece o
segredo daquela conta. O arquivo nunca guarda o PIN em texto puro e não existe
uma operação para listar os identificadores cadastrados.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
from pathlib import Path

from jarvis.nucleo.caminhos import PASTA_DADOS

CAMINHO_CREDENCIAIS = PASTA_DADOS / "acesso_pin.json"
ITERACOES = 200_000
PADRAO_IDENTIFICADOR = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._@+-]{2,63}")
PADRAO_PIN = re.compile(r"\d{6}")


class IdentificadorInvalidoError(ValueError):
    """O identificador não pode ser usado como chave de login."""


class PinInvalidoError(ValueError):
    """O PIN não tem exatamente seis dígitos."""


class IdentificadorEmUsoError(ValueError):
    """O identificador já pertence a outro usuário."""


class AcessoPin:
    """Persistência mínima e privada das credenciais de acesso alternativo."""

    def __init__(self, caminho: Path = CAMINHO_CREDENCIAIS) -> None:
        self._caminho = caminho

    def configurar(self, identificador: str, usuario: str, pin: str) -> None:
        chave = normalizar_identificador(identificador)
        validar_pin(pin)
        dados = self._ler()
        existente = dados["credenciais"].get(chave)
        if existente is not None and existente["usuario"] != usuario:
            raise IdentificadorEmUsoError("Esse identificador já está vinculado a outro usuário.")

        salt = os.urandom(16)
        digest = _derivar(pin, salt)
        dados["credenciais"][chave] = {
            "usuario": usuario,
            "salt": salt.hex(),
            "digest": digest.hex(),
        }
        self._escrever(dados)

    def autenticar(self, identificador: str, pin: str) -> str | None:
        try:
            chave = normalizar_identificador(identificador)
            validar_pin(pin)
        except (IdentificadorInvalidoError, PinInvalidoError):
            return None

        registro = self._ler()["credenciais"].get(chave)
        if registro is None:
            return None

        try:
            esperado = bytes.fromhex(registro["digest"])
            salt = bytes.fromhex(registro["salt"])
        except (KeyError, ValueError):
            return None

        atual = _derivar(pin, salt)
        return registro["usuario"] if hmac.compare_digest(atual, esperado) else None

    def configurado_para(self, usuario: str) -> bool:
        return any(
            registro.get("usuario") == usuario for registro in self._ler()["credenciais"].values()
        )

    def _ler(self) -> dict[str, object]:
        if not self._caminho.exists():
            return {"versao": 1, "credenciais": {}}
        try:
            dados = json.loads(self._caminho.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"versao": 1, "credenciais": {}}
        credenciais = dados.get("credenciais")
        if not isinstance(credenciais, dict):
            return {"versao": 1, "credenciais": {}}
        return {"versao": 1, "credenciais": credenciais}

    def _escrever(self, dados: dict[str, object]) -> None:
        self._caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = self._caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporario.replace(self._caminho)


def normalizar_identificador(identificador: str) -> str:
    valor = identificador.strip().casefold()
    if not PADRAO_IDENTIFICADOR.fullmatch(valor):
        raise IdentificadorInvalidoError("Use um identificador com 3 a 64 caracteres, sem espaços.")
    return valor


def validar_pin(pin: str) -> str:
    if not PADRAO_PIN.fullmatch(pin):
        raise PinInvalidoError("O PIN precisa ter exatamente 6 dígitos.")
    return pin


def _derivar(pin: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", pin.encode("utf-8"), salt, ITERACOES, dklen=32)
