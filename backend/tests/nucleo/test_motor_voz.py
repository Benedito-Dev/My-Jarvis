import pytest

from jarvis.nucleo.motor_voz import MotorIndisponivelError, escolher

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
