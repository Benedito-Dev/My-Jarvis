import os
import wave

import numpy as np

from jarvis.nucleo.voz_piper import VozPiper, envelope, nome_no_cache


class SinteseFalsa:
    """Escreve o texto no arquivo em vez de gerar áudio, e conta as chamadas."""

    def __init__(self):
        self.carregou = 0
        self.geradas = []

    def carregar(self):
        self.carregou += 1
        return self.sintetizar

    def sintetizar(self, frase, destino):
        self.geradas.append(frase)
        destino.write_text(frase)


def test_gera_o_audio_da_frase(tmp_path):
    sintese = SinteseFalsa()
    voz = VozPiper(tmp_path, carregar=sintese.carregar)

    arquivo = voz.arquivo_da_frase("Bem-vindo, Benedito")

    assert arquivo.read_text() == "Bem-vindo, Benedito"
    assert arquivo.suffix == ".wav"


def test_a_mesma_frase_sai_do_cache(tmp_path):
    sintese = SinteseFalsa()
    voz = VozPiper(tmp_path, carregar=sintese.carregar)

    primeiro = voz.arquivo_da_frase("São 14 horas e 3.")
    segundo = voz.arquivo_da_frase("São 14 horas e 3.")

    assert primeiro == segundo
    assert sintese.geradas == ["São 14 horas e 3."]


def test_so_carrega_o_modelo_quando_precisa_e_uma_vez(tmp_path):
    sintese = SinteseFalsa()
    voz = VozPiper(tmp_path, carregar=sintese.carregar)
    assert sintese.carregou == 0  # criar é de graça

    voz.preparar(["um", "dois", "três"])

    assert sintese.carregou == 1
    assert sintese.geradas == ["um", "dois", "três"]


def test_nao_deixa_arquivo_pela_metade(tmp_path):
    voz = VozPiper(tmp_path, carregar=lambda: SinteseFalsa().sintetizar)

    voz.arquivo_da_frase("oi")

    assert [p.name for p in tmp_path.iterdir()] == [nome_no_cache("oi")]


def test_cache_tem_limite_e_tira_as_usadas_ha_mais_tempo(tmp_path):
    voz = VozPiper(tmp_path, carregar=lambda: SinteseFalsa().sintetizar, maximo_no_cache=2)
    antiga = voz.arquivo_da_frase("antiga")
    os.utime(antiga, (1, 1))  # usada há muito tempo
    voz.arquivo_da_frase("recente")

    voz.arquivo_da_frase("nova")

    assert not antiga.exists()
    assert len(list(tmp_path.glob("*.wav"))) == 2


def test_frases_diferentes_caem_em_arquivos_diferentes():
    assert nome_no_cache("Bloqueando.") != nome_no_cache("Bem-vindo.")


def test_envelope_segue_o_volume_do_audio(tmp_path):
    taxa = 22050
    silencio = np.zeros(int(taxa * 0.08), dtype=np.int16)  # 2 janelas de 40 ms
    alto = (np.sin(np.linspace(0, 400, int(taxa * 0.08))) * 32767 * 0.5).astype(np.int16)
    arquivo = tmp_path / "fala.wav"
    with wave.open(str(arquivo), "wb") as saida:
        saida.setnchannels(1)
        saida.setsampwidth(2)
        saida.setframerate(taxa)
        saida.writeframes(np.concatenate([silencio, alto]).tobytes())

    niveis = envelope(arquivo)

    assert niveis[:2] == [0.0, 0.0]  # silêncio
    assert min(niveis[2:4]) > 0.9  # seno com metade do volume máximo: bem acima da fala normal
    assert all(0 <= n <= 1 for n in niveis)
