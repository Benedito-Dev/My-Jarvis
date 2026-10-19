from pathlib import Path

import pytest

from jarvis.nucleo.motor_voz import MotorIndisponivelError, comando_tocar, escolher

# A plataforma é sempre passada à mão: assim estes testes valem para os três
# sistemas, rodando em qualquer máquina.


def test_no_macos_fala_com_o_say():
    motor = escolher("darwin")

    assert motor.falar("Olá") == ["say", "-v", "Luciana", "Olá"]


def test_no_macos_matar_o_processo_basta_para_calar():
    assert escolher("darwin").cancelar is None


def test_no_linux_fala_com_o_spd_say_esperando_terminar():
    motor = escolher("linux")

    # O -w é o que faz o comando durar o tempo da fala.
    assert motor.falar("Olá") == ["spd-say", "-w", "-l", "pt", "Olá"]


def test_no_linux_calar_precisa_de_um_comando_proprio():
    assert escolher("linux").cancelar == ["spd-say", "-C"]


def test_a_voz_pode_ser_trocada_por_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("JARVIS_VOZ", "Felipe")

    assert escolher("darwin").falar("Olá") == ["say", "-v", "Felipe", "Olá"]


def test_sistema_sem_motor_avisa():
    with pytest.raises(MotorIndisponivelError):
        escolher("win32")


# --- Voz Piper: a mesma nos três sistemas; só o tocador muda ------------------


class VozPiperFalsa:
    def arquivo_da_frase(self, frase):
        return Path(f"/cache/{frase}.wav")

    def preparar(self, frases):
        pass


@pytest.mark.parametrize(
    ("plataforma", "comando"),
    [
        ("darwin", ["afplay", "/cache/Olá.wav"]),
        ("linux", ["paplay", "/cache/Olá.wav"]),
    ],
)
def test_com_piper_toca_o_audio_gerado(plataforma, comando):
    motor = escolher(plataforma, voz_piper=VozPiperFalsa(), existe=lambda _: "/usr/bin/x")

    assert motor.nome == "piper"
    assert motor.falar("Olá") == comando


def test_no_windows_o_piper_toca_pelo_powershell():
    motor = escolher("win32", voz_piper=VozPiperFalsa())

    comando = motor.falar("Olá")
    assert comando[0] == "powershell"
    assert "PlaySync" in comando[-1]


def test_no_linux_usa_o_tocador_que_existir():
    so_aplay = lambda programa: "/usr/bin/aplay" if programa == "aplay" else None  # noqa: E731

    motor = escolher("linux", voz_piper=VozPiperFalsa(), existe=so_aplay)

    assert motor.falar("Olá") == ["aplay", "-q", "/cache/Olá.wav"]


def test_linux_sem_tocador_avisa():
    with pytest.raises(MotorIndisponivelError):
        comando_tocar("linux", existe=lambda _: None)
