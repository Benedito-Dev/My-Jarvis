from fastapi.testclient import TestClient

from jarvis.api import criar_app
from jarvis.nucleo.acesso_pin import AcessoPin


def cliente_com_pin(tmp_path):
    acesso_pin = AcessoPin(tmp_path / "acesso_pin.json")
    acesso_pin.configurar("benedito", "benedito", "123456")
    return TestClient(criar_app(pasta_rostos=tmp_path / "rostos", acesso_pin=acesso_pin))


def test_login_por_pin_nao_expoe_perfis_antes_da_autenticacao(tmp_path):
    cliente = cliente_com_pin(tmp_path)

    resposta = cliente.get("/rostos")

    assert resposta.status_code == 401
    assert "cadastrados" not in resposta.json()


def test_login_por_pin_desbloqueia_com_identificador_digitado(tmp_path):
    cliente = cliente_com_pin(tmp_path)

    resposta = cliente.post(
        "/sessao/pin",
        json={"identificador": "Benedito", "pin": "123456"},
    )

    assert resposta.status_code == 200
    assert resposta.json() == {"usuario": "Benedito"}
    assert cliente.get("/sessao").json() == {"usuario": "Benedito"}


def test_login_por_pin_nao_diz_qual_credencial_falhou(tmp_path):
    cliente = cliente_com_pin(tmp_path)

    resposta = cliente.post(
        "/sessao/pin",
        json={"identificador": "nao-existe", "pin": "123456"},
    )

    assert resposta.status_code == 401
    assert resposta.json() == {"detail": "Identificador ou PIN inválido."}


def test_pin_pode_ser_configurado_somente_depois_do_login(tmp_path):
    cliente = cliente_com_pin(tmp_path)

    bloqueado = cliente.post(
        "/sessao/pin/configurar",
        json={"identificador": "novo", "pin": "654321"},
    )
    assert bloqueado.status_code == 401

    cliente.post("/sessao/pin", json={"identificador": "benedito", "pin": "123456"})
    configurado = cliente.post(
        "/sessao/pin/configurar",
        json={"identificador": "novo", "pin": "654321"},
    )

    assert configurado.status_code == 200
    cliente.post("/sessao/bloquear")
    assert cliente.post("/sessao/pin", json={"identificador": "novo", "pin": "654321"}).json() == {
        "usuario": "Benedito"
    }
