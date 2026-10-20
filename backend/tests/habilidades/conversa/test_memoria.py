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


def test_guarda_a_troca_com_ferramentas():
    memoria = Memoria(relogio=Relogio())
    troca = [
        {"role": "user", "content": "abre o Spotify"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "c1"}]},
        {"role": "tool", "tool_call_id": "c1", "content": "Spotify aberto."},
        {"role": "assistant", "content": "Abrindo o Spotify."},
    ]

    memoria.lembrar_troca(troca)

    assert memoria.recentes() == troca


def test_resultado_grande_de_ferramenta_e_encurtado():
    memoria = Memoria(relogio=Relogio())
    memoria.lembrar_troca(
        [
            {"role": "user", "content": "pesquisa"},
            {"role": "tool", "tool_call_id": "c1", "content": "x" * 5000},
        ]
    )

    assert len(memoria.recentes()[1]["content"]) < 400
