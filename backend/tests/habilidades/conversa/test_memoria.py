from jarvis.habilidades.conversa.memoria import Memoria


class Relogio:
    def __init__(self):
        self.agora = 0.0

    def __call__(self):
        return self.agora


def test_devolve_as_trocas_como_mensagens():
    memoria = Memoria(relogio=Relogio())
    memoria.lembrar("que dia é hoje?", "Hoje é terça-feira, 20 de outubro.")

    assert memoria.recentes() == [
        {"role": "user", "content": "que dia é hoje?"},
        {"role": "assistant", "content": "Hoje é terça-feira, 20 de outubro."},
    ]


def test_guarda_so_as_ultimas_trocas():
    memoria = Memoria(maximo_de_trocas=2, relogio=Relogio())
    for i in range(3):
        memoria.lembrar(f"p{i}", f"r{i}")

    assert [m["content"] for m in memoria.recentes()] == ["p1", "r1", "p2", "r2"]


def test_esquece_depois_de_um_tempo_parado():
    relogio = Relogio()
    memoria = Memoria(esquecer_apos_s=600, relogio=relogio)
    memoria.lembrar("oi", "olá")

    relogio.agora = 601

    assert memoria.recentes() == []


def test_esquecer_apaga_tudo():
    memoria = Memoria(relogio=Relogio())
    memoria.lembrar("oi", "olá")

    memoria.esquecer()

    assert memoria.recentes() == []
