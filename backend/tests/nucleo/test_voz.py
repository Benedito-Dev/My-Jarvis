from jarvis.nucleo.motor_voz import MotorDeVoz
from jarvis.nucleo.voz import SEGUNDOS_ENTRE_REPETICOES, Locutor

# Motor de mentira: estes testes são sobre as regras de *quando* falar, não
# sobre o comando de cada sistema (isso é do test_motor_voz.py). Com o motor
# injetado, a suíte passa igual no Mac, no Linux e no Windows.
MOTOR_FALSO = MotorDeVoz(nome="falso", programa="falar", falar=lambda frase: ["falar", frase])
MOTOR_QUE_PRECISA_CANCELAR = MotorDeVoz(
    nome="falso-com-cancelar",
    programa="falar",
    falar=lambda frase: ["falar", frase],
    cancelar=["calar"],
)


class ProcessoFalso:
    def __init__(self) -> None:
        self.terminou = False
        self.interrompido = False

    def wait(self):
        self.terminou = True  # nos testes, a fala "acaba" na hora

    def poll(self):
        return 0 if self.terminou else None

    def terminate(self) -> None:
        self.interrompido = True
        self.terminou = True


class Cenario:
    """Locutor com motor de mentira e relógio de mentira."""

    def __init__(self, motor: MotorDeVoz = MOTOR_FALSO) -> None:
        self.agora = 0.0
        self.comandos: list[list[str]] = []
        self.processos: list[ProcessoFalso] = []
        self.adiadas = []  # tarefas "em fundo": o teste decide quando rodar
        self.locutor = Locutor(
            motor=motor,
            iniciar=self._iniciar,
            relogio=lambda: self.agora,
            em_fundo=self.adiadas.append,
        )

    def rodar_em_fundo(self) -> None:
        while self.adiadas:
            self.adiadas.pop(0)()

    def _iniciar(self, comando):
        self.comandos.append(comando)
        self.processos.append(ProcessoFalso())
        return self.processos[-1]

    def terminar_fala(self) -> None:
        self.processos[-1].terminou = True


def test_fala_usando_o_comando_do_motor():
    cenario = Cenario()

    assert cenario.locutor.falar("Olá")
    assert cenario.comandos == [["falar", "Olá"]]


def test_ignora_frase_nova_enquanto_fala():
    cenario = Cenario()
    cenario.locutor.falar("Primeira")

    assert not cenario.locutor.falar("Segunda")
    assert len(cenario.comandos) == 1


def test_interromper_corta_a_fala_atual():
    cenario = Cenario()
    cenario.locutor.falar("Aproxime seu rosto")

    assert cenario.locutor.falar("Bem-vindo", interromper=True)
    assert cenario.processos[0].interrompido
    assert cenario.comandos[-1] == ["falar", "Bem-vindo"]


def test_interromper_usa_o_cancelar_do_motor_quando_existe():
    cenario = Cenario(motor=MOTOR_QUE_PRECISA_CANCELAR)
    cenario.locutor.falar("Aproxime seu rosto")

    assert cenario.locutor.falar("Bem-vindo", interromper=True)
    # Matar o processo não basta neste motor: o cancelar roda antes da nova fala.
    assert cenario.comandos == [["falar", "Aproxime seu rosto"], ["calar"], ["falar", "Bem-vindo"]]


def test_nao_repete_a_mesma_frase_logo_em_seguida():
    cenario = Cenario()
    cenario.locutor.falar("Aproxime seu rosto")
    cenario.terminar_fala()

    cenario.agora = SEGUNDOS_ENTRE_REPETICOES - 1
    assert not cenario.locutor.falar("Aproxime seu rosto")

    cenario.agora = SEGUNDOS_ENTRE_REPETICOES + 1
    assert cenario.locutor.falar("Aproxime seu rosto")


def test_frase_diferente_nao_precisa_esperar():
    cenario = Cenario()
    cenario.locutor.falar("Aproxime seu rosto")
    cenario.terminar_fala()

    assert cenario.locutor.falar("Acesso negado")


def test_sem_motor_fica_mudo_mas_nao_quebra():
    locutor = Locutor(motor=None, iniciar=_nao_deve_ser_chamado)

    assert locutor.muda
    assert not locutor.falar("Bem-vindo", interromper=True)


def _nao_deve_ser_chamado(comando):
    raise AssertionError(f"Locutor mudo não deveria rodar nada, mas rodou {comando}")


def test_fica_mudo_se_o_programa_de_voz_nao_esta_instalado(monkeypatch):
    # Ex.: Linux sem spd-say. Antes, o primeiro "Bem-vindo" levantava FileNotFoundError.
    monkeypatch.delenv("JARVIS_MUDO")  # aqui queremos o caminho de verdade
    monkeypatch.setattr("jarvis.nucleo.voz.shutil.which", lambda _programa: None)

    locutor = Locutor()

    assert locutor.muda
    assert not locutor.falar("Bem-vindo")


# --- Fila de fala (respostas em pedaços) ---------------------------------------


def test_fila_fala_as_frases_em_ordem():
    cenario = Cenario()

    cenario.locutor.enfileirar("Primeira frase.")
    cenario.locutor.enfileirar("Segunda frase.")
    cenario.rodar_em_fundo()

    assert cenario.comandos == [["falar", "Primeira frase."], ["falar", "Segunda frase."]]


def test_interromper_esvazia_a_fila():
    cenario = Cenario()
    cenario.locutor.enfileirar("Resposta antiga, parte um.")
    cenario.locutor.enfileirar("Resposta antiga, parte dois.")

    cenario.locutor.falar("Bem-vindo", interromper=True)
    cenario.rodar_em_fundo()

    assert ["falar", "Resposta antiga, parte dois."] not in cenario.comandos


def test_resposta_nova_depois_de_interromper_toca_mesmo_assim():
    # A fila antiga ainda não percebeu a interrupção; a nova não pode ficar sem tocar.
    cenario = Cenario()
    cenario.locutor.enfileirar("Antiga.")
    cenario.locutor.falar("Interrompe", interromper=True)
    cenario.locutor.enfileirar("Nova resposta.")
    cenario.rodar_em_fundo()

    assert ["falar", "Nova resposta."] in cenario.comandos
    assert ["falar", "Antiga."] not in cenario.comandos


def test_fila_sem_motor_nao_faz_nada():
    locutor = Locutor(motor=None)

    locutor.enfileirar("oi")  # não quebra
