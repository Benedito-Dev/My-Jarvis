"""Download de arquivos grandes (ex.: modelos de IA) com verificação de integridade."""

import hashlib
import urllib.request
from pathlib import Path


class ArquivoCorrompidoError(RuntimeError):
    """O arquivo baixado não bate com o hash esperado."""


def calcular_sha256(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def baixar_se_necessario(url: str, destino: Path, sha256: str) -> Path:
    """Baixa `url` para `destino` só se ainda não existir, e confere o SHA-256.

    O download vai para um arquivo temporário e só é renomeado depois de
    verificado. Assim, um download interrompido nunca deixa um arquivo pela metade.
    """
    if destino.exists():
        return destino

    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(destino.suffix + ".parcial")
    print(f"Baixando {destino.name} (só na primeira vez)...")
    try:
        urllib.request.urlretrieve(url, temporario)
        obtido = calcular_sha256(temporario)
        if obtido != sha256:
            raise ArquivoCorrompidoError(
                f"{destino.name}: hash esperado {sha256}, obtido {obtido}. Tente novamente."
            )
        temporario.replace(destino)
    finally:
        temporario.unlink(missing_ok=True)
    return destino
