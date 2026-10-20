import subprocess

import pytest

from jarvis.nucleo.sistema import (
    NaoConsigoAbrirError,
    abrir,
    comando_abrir_app,
    comando_abrir_site,
    normalizar_endereco,
)


def test_endereco_sem_protocolo_ganha_https():
    assert normalizar_endereco("youtube.com") == "https://youtube.com"


@pytest.mark.parametrize(
    "ruim", ["file:///etc/passwd", "javascript:alert(1)", "sem ponto", "a b.com"]
)
def test_recusa_endereco_estranho(ruim):
    with pytest.raises(NaoConsigoAbrirError):
        normalizar_endereco(ruim)


@pytest.mark.parametrize(
    ("plataforma", "comando"),
    [
        ("darwin", ["open", "https://youtube.com/results?q=a&b=c"]),
        ("linux", ["xdg-open", "https://youtube.com/results?q=a&b=c"]),
        (
            "win32",
            ["rundll32", "url.dll,FileProtocolHandler", "https://youtube.com/results?q=a&b=c"],
        ),
    ],
)
def test_abrir_site_em_cada_sistema(plataforma, comando):
    assert comando_abrir_site("youtube.com/results?q=a&b=c", plataforma) == comando


def test_abrir_app_no_mac_e_no_windows():
    assert comando_abrir_app("Visual Studio Code", "darwin") == ["open", "-a", "Visual Studio Code"]
    assert comando_abrir_app("Spotify", "win32") == ["cmd", "/c", "start", "", "Spotify"]


def test_abrir_app_no_linux_procura_o_programa():
    existe = {"vs-code": "/usr/bin/vs-code"}.get

    assert comando_abrir_app("VS Code", "linux", existe) == ["/usr/bin/vs-code"]


def test_app_que_nao_existe_no_linux():
    with pytest.raises(NaoConsigoAbrirError):
        comando_abrir_app("Spotify", "linux", lambda _: None)


@pytest.mark.parametrize("injecao", ["Spotify & del C:\\", "x; rm -rf ~", "a|b", "$(whoami)", ""])
def test_recusa_nome_de_app_com_truques(injecao):
    with pytest.raises(NaoConsigoAbrirError):
        comando_abrir_app(injecao, "win32")


def test_abrir_falhou_vira_erro():
    def rodar_que_falha(comando, **_):
        return subprocess.CompletedProcess(comando, returncode=1)

    with pytest.raises(NaoConsigoAbrirError):
        abrir(["open", "-a", "Nada"], rodar=rodar_que_falha)
