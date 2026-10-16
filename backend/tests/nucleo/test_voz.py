from jarvis.nucleo.voz import SEGUNDOS_ENTRE_REPETICOES, Locutor


class ProcessoFalso:
    def __init__(self) -> None:
        self.terminou = False
        self.interrompido = False

    def poll(self):
        return 0 if self.terminou else None

    def terminate(self) -> None:
        self.interrompido = True
        self.terminou = True


class Cenario:
    """Locutor com `say` e relógio de mentira."""

    def __init__(self) -> None:
        self.agora = 0.0
        self.comandos: list[list[str]] = []
        self.processos: list[ProcessoFalso] = []
        self.locutor = Locutor(voz="Luciana", iniciar=self._iniciar, relogio=lambda: self.agora)

    def _iniciar(self, comando):
        self.comandos.append(comando)
        self.processos.append(ProcessoFalso())
        return self.processos[-1]

    def terminar_fala(self) -> None:
        self.processos[-1].terminou = True


def test_fala_com_o_comando_say():
    cenario = Cenario()

    assert cenario.locutor.falar("Olá")
    assert cenario.comandos == [["say", "-v", "Luciana", "Olá"]]


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
    assert cenario.comandos[-1][-1] == "Bem-vindo"


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
