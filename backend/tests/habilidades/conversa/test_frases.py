from jarvis.habilidades.conversa.frases import fatiar


def test_separa_frases_completas_do_resto():
    prontas, resto = fatiar("Claro, senhor, um omelete resolve. Fica pronto em cinco min")

    assert prontas == ["Claro, senhor, um omelete resolve."]
    assert resto == "Fica pronto em cinco min"


def test_frase_curta_espera_juntar_com_a_proxima():
    prontas, resto = fatiar("Sim. O jogo é às quatro da tarde. E")

    assert prontas == ["Sim. O jogo é às quatro da tarde."]
    assert resto == "E"


def test_sem_frase_fechada_nada_fica_pronto():
    assert fatiar("Que tal um macarrão") == ([], "Que tal um macarrão")


def test_nao_corta_numero_com_ponto():
    prontas, _ = fatiar("A distância é de 384.400 quilômetros, em média. Depois")

    assert prontas == ["A distância é de 384.400 quilômetros, em média."]


def test_pergunta_e_exclamacao_fecham_frase():
    prontas, _ = fatiar("Quer que eu te avise antes do jogo? Posso avisar dez minutos antes! ")

    assert prontas == [
        "Quer que eu te avise antes do jogo?",
        "Posso avisar dez minutos antes!",
    ]
