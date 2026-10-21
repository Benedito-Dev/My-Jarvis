"""Treina o detector de "Jarvis" com a voz do dono (decisão 0023).

Uso, dentro de backend/:

    uv run --with scikit-learn python ferramentas/treinar_escuta.py            # treina
    uv run --with scikit-learn python ferramentas/treinar_escuta.py --avaliar  # só mede

O que ele faz:
1. Gera falas sintéticas com "Jarvis" e sem (vozes Piper e, no macOS, as do
   sistema). Só na primeira vez: baixa ~380 MB de vozes e leva ~20 min. Fica
   tudo em dados/escuta/treino/, para as próximas vezes serem rápidas.
2. Lê as suas gravações (dados/gravacoes/), que o Whisper transcreve para saber
   quais têm "Jarvis" e onde o nome termina.
3. Treina a rede pequena e salva em dados/escuta/jarvis.npz (o anterior vira
   jarvis.anterior.npz). Reinicie o app para usar o novo.

Quanto mais você conversa com o Jarvis, mais gravações suas existem e melhor
fica o detector: vale rodar de novo de tempos em tempos.

`--avaliar` divide as suas gravações em duas metades, treina com uma e testa na
outra (e vice-versa): é a medida honesta de quantos "Jarvis" ele acha e de
quantos alarmes falsos dá. Não troca o detector em uso.
"""

import argparse
import json
import random
import re
import shutil
import subprocess
import sys
import urllib.request
import wave
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from pathlib import Path

import numpy as np

from jarvis.habilidades.escuta import detector
from jarvis.nucleo import voz_piper
from jarvis.nucleo.arquivos import baixar_se_necessario
from jarvis.nucleo.caminhos import PASTA_DADOS

TAXA = detector.TAXA
JANELA = detector.JANELA
DURACAO_S = 3.0  # cada exemplo: 3 s de som, com o fim do "Jarvis" perto do fim

PASTA = PASTA_DADOS / "escuta" / "treino"
PASTA_VOZES = PASTA / "vozes"
PASTA_SINTETICAS = PASTA / "sinteticas"
CACHE_SINTETICOS = PASTA / "caracteristicas_sinteticas.npz"
CACHE_TRANSCRICOES = PASTA / "transcricoes.json"
PASTA_GRAVACOES = PASTA_DADOS / "gravacoes"

_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
# Vozes para variar quem diz "Jarvis": 4 em português e uma inglesa com 900 falantes.
VOZES = {
    "pt_BR-cadu-medium": (
        "pt/pt_BR/cadu/medium",
        "765f0809a6ea9035d4a6d0d008dbf8876e68b2dd32029312672fa8f405bdb535",
        "5fe03aa3d4901880554905b12075713cd552598c8a350455a1ec73f8b4e6be19",
    ),
    "pt_BR-jeff-medium": (
        "pt/pt_BR/jeff/medium",
        "3a6f4c46355813c2b7bbc4d16b6d13d60ed72074b952a393baace82a7d0c94b5",
        "7bf8145b572b36806f5ce0f1d3322b6711975bc7d0473e8d36fced4a9ec0030d",
    ),
    "pt_BR-edresson-low": (
        "pt/pt_BR/edresson/low",
        "de4cecee38b30bb1a6378a337af605d59f0c377df702c6a6752870db8991cd84",
        "f138992d2e777d1e3aa0bbb14c2d324307b0f342c1bcf20978765b3bea506c56",
    ),
    "pt_PT-tugão-medium": (
        "pt/pt_PT/tugão/medium",
        "223a7aaca69a155c61897e8ada7c3b13bc306e16c72dbb9c2fed733e2b0927d4",
        "fe0918dfc0f1a89264a6eea4afe8e95d8e9fed3cc6c81b5c2f87fcb2b50c7320",
    ),
    "en_US-libritts_r-medium": (
        "en/en_US/libritts_r/medium",
        "10bb85e071d616fcf4071f369f1799d0491492ab3c5d552ec19fb548fac13195",
        "b471dc60d2d8335e819c393d196d6fbf792817f40051257b269878505bc9afb3",
    ),
}
VOZES_DO_MACOS = ["Luciana", "Joana", "Samantha", "Daniel", "Karen", "Moira", "Tessa", "Fred"]

COM_JARVIS = ["Jarvis", "Jarvis.", "Jarvis!", "Ei, Jarvis", "Ô Jarvis", "Bom dia, Jarvis",
              "Olá Jarvis", "E aí, Jarvis", "Fala, Jarvis", "Járvis"]  # fmt: skip
COM_JARVIS_EN = ["Jarvis", "Hey Jarvis", "Jarvis.", "Okay Jarvis"]
SEM_JARVIS_EN = ["Travis", "Garbage", "Service", "Jar of beans", "Harvest", "Marvelous",
                 "The news tonight", "Turn on the lights", "Good morning",
                 "What time is it"]  # fmt: skip
# Falas do dia a dia e palavras parecidas com "Jarvis" (as que mais confundem).
SEM_JARVIS = """Bom dia|Boa tarde, tudo bem?|Que horas são?|Como está o clima hoje?
Me lembra de ligar pro dentista|Vamos almoçar?|O jogo começa às oito horas
Hoje vai chover à tarde|Você viu o jornal ontem?|A reunião foi adiada para amanhã
Preciso comprar pão e leite|O ônibus atrasou de novo|Liga a televisão por favor
Abre a janela que está calor|O presidente falou sobre a economia|O dólar subiu nesta manhã
A seleção venceu o amistoso|Fortaleza tem praias lindas|O Ceará empatou no Castelão
Amanhã eu acordo cedo|Onde você deixou a chave do carro?|Eu vou tomar banho e já volto
Coloca uma música aí|Desliga a luz da sala|A comida está pronta|Quanto custa esse celular?
Meu irmão chega no sábado|A previsão é de sol com nuvens|O trânsito está parado na avenida
Vou dormir mais um pouco|Já vi esse filme duas vezes|Já vi isso antes|Travis|Chaves|Jarbas
Jardim|Jair|Davi|Marvin|Garagem|Jaqueta azul|Carlos|Jardins do Ceará|Já disse que não|Já vou
Gravei o programa|O Jair saiu cedo|Já é tarde demais|A gente se vê depois|Obrigado pela ajuda
Esse é o meu amigo Travis|Ele mora no Jardim América|O Chaves passa na televisão
Vamos ver o jogo do Barcelona|Bloquear|Bloqueia a tela|Desce, desce|Alô, alô|Olá, tudo bom?
Corre, corre|Cuidado com o degrau|Eu acho que vai dar certo|Ela comprou flores no mercado
A escola fecha nas férias|Meu cachorro late muito|O avião decolou às seis
Precisamos conversar sobre o projeto|Você pode repetir, por favor?|Não entendi o que você falou
Isso é muito interessante|Vamos marcar para semana que vem|O médico pediu exames
O preço da gasolina caiu|As eleições são no domingo|A polícia prendeu o suspeito
O show foi cancelado por causa da chuva|Que dia é hoje?|Qual é a temperatura agora?
Tem notícia nova?|Abre o Spotify|Anota aí: comprar café|Quanto é dez vezes doze?
Me conta uma piada|Pausa a música|Volta a música|Próxima faixa|Aumenta o volume|Baixa o volume
Já vi|Já vis|Já avisei|Aviso|Davis|Harvey|Javier|Xavier|Jarro|Jarros|Jarras|Chaveiro|Vírus
Garfo|Jarvas|Jervis|Gervásio|Carlos Alberto|Já viu isso?|Já é|Já falei|Arvoredo|Servis
Jarbas Passarinho""".replace("\n", "|").split("|")
# Mais falas variadas, das manchetes de agora (se houver internet).
FEEDS = [
    "https://news.google.com/rss?hl=pt-BR&gl=BR&ceid=BR:pt-419",
    "https://g1.globo.com/rss/g1/",
    "https://feeds.folha.uol.com.br/emcimadahora/rss091.xml",
]

rng = np.random.default_rng(7)
random.seed(7)


# --- Som ------------------------------------------------------------------------------


def ler_wav(caminho: Path) -> np.ndarray:
    """Um .wav qualquer → float32 em 16 kHz, mono, de -1 a 1."""
    with wave.open(str(caminho)) as arquivo:
        taxa = arquivo.getframerate()
        canais = arquivo.getnchannels()
        som = np.frombuffer(arquivo.readframes(arquivo.getnframes()), np.int16)
    som = som[::canais].astype(np.float32) / 32768
    if taxa != TAXA:
        from scipy.signal import resample_poly  # vem junto do scikit-learn

        divisor = np.gcd(TAXA, taxa)
        som = resample_poly(som, TAXA // divisor, taxa // divisor).astype(np.float32)
    return som


def normalizar(som: np.ndarray, aparar: bool = True) -> np.ndarray:
    """Pico em 1 e, se `aparar`, sem o silêncio das pontas."""
    som = som / (np.abs(som).max() + 1e-6)
    if aparar:
        alto = np.abs(som) > 0.02
        if alto.any():
            inicio, fim = np.argmax(alto), len(alto) - np.argmax(alto[::-1])
            som = som[max(0, inicio - 800) : fim + 800]
    return som


def ruido(n: int) -> np.ndarray:
    branco = rng.standard_normal(n)
    if rng.random() < 0.5:  # ruído "rosa": mais grave, como ventilador e ar-condicionado
        branco = np.cumsum(branco)
        branco -= np.convolve(branco, np.ones(400) / 400, "same")
    return branco / (np.abs(branco).max() + 1e-6)


def com_eco(som: np.ndarray) -> np.ndarray:
    from scipy.signal import fftconvolve

    tamanho = int(TAXA * rng.uniform(0.1, 0.4))
    sala = rng.standard_normal(tamanho) * np.exp(-np.linspace(0, rng.uniform(4, 10), tamanho))
    sala[0] = 1
    saida = fftconvolve(som, sala)[: len(som)]
    return saida / (np.abs(saida).max() + 1e-6)


def variar(som: np.ndarray, fundo: np.ndarray | None = None) -> np.ndarray:
    """O mesmo som, como se dito em outra sala: eco, volume e barulho de fundo."""
    if rng.random() < 0.5:
        som = com_eco(som)
    som = som * rng.uniform(0.2, 1.0)
    fundo = ruido(len(som)) if fundo is None else np.resize(fundo, len(som))
    forca = np.sqrt(np.mean(som**2)) / (np.sqrt(np.mean(fundo**2)) + 1e-6)
    return som + fundo * forca / 10 ** (rng.uniform(5, 30) / 20) * rng.uniform(0, 1)


def encaixar(som: np.ndarray, com_jarvis: bool, continuacoes: list[np.ndarray]) -> np.ndarray:
    """Põe o som numa janela de 3 s. Com "Jarvis", o nome termina perto do fim
    (é ali que o detector precisa disparar) e, metade das vezes, o pedido
    começa logo depois, como na vida real ("Jarvis, que horas são?")."""
    n = int(TAXA * DURACAO_S)
    saida = np.zeros(n, np.float32)
    if com_jarvis:
        fim = n - int(TAXA * rng.uniform(0.05, 0.35))
        inicio = max(0, fim - len(som))
        saida[inicio:fim] = som[-(fim - inicio) :]
        if continuacoes and rng.random() < 0.5:
            pedido = random.choice(continuacoes) * rng.uniform(0.5, 1.0)
            comeco = fim + int(TAXA * rng.uniform(0.0, 0.15))
            cabe = min(len(pedido), n - comeco)
            if cabe > 0:
                saida[comeco : comeco + cabe] = pedido[:cabe]
    elif len(som) >= n:
        inicio = rng.integers(0, len(som) - n + 1)
        saida[:] = som[inicio : inicio + n]
    else:
        inicio = rng.integers(0, n - len(som) + 1)
        saida[inicio : inicio + len(som)] = som
    return saida


# --- Características (as mesmas do detector, em lote) -----------------------------------


class Caracteristicas:
    """O que o detector vê, calculado de uma vez para muitos sons iguais em tamanho."""

    def __init__(self) -> None:
        detector.Caracteristicas()  # baixa os modelos, se preciso
        import onnxruntime as ort

        self._espectrograma = ort.InferenceSession(str(detector.ESPECTROGRAMA))
        self._embedding = ort.InferenceSession(str(detector.EMBEDDING))

    def linhas(self, sons: np.ndarray) -> np.ndarray:
        """(N, amostras) float → (N, linhas, 96): uma linha a cada 80 ms."""
        pcm = (np.clip(sons, -1, 1) * 32767).astype(np.int16).astype(np.float32)
        saida = []
        for inicio in range(0, len(pcm), 64):
            lote = pcm[inicio : inicio + 64]
            espectro = self._espectrograma.run(None, {"input": lote})[0]
            quadros = np.squeeze(espectro, axis=1) / 10 + 2  # (lote, quadros, 32)
            q = detector.QUADROS_POR_EMBEDDING
            janelas = [
                quadros[:, i : i + q] for i in range(0, quadros.shape[1] - q + 1, 8)
            ]  # a cada 8 quadros (80 ms)
            pilha = np.stack(janelas, axis=1).reshape(-1, q, 32, 1).astype(np.float32)
            emb = self._embedding.run(None, {"input_1": pilha})[0]
            saida.append(emb.reshape(len(lote), len(janelas), -1))
        return np.concatenate(saida)

    def exemplos(self, sons: Iterable[np.ndarray]) -> np.ndarray:
        """Cada som de 3 s → as últimas 16 linhas, achatadas: o que o detector julga.

        Consome os sons aos poucos: 13 mil sons de 3 s juntos ocupariam ~2,6 GB.
        """
        partes, lote = [], []
        for som in sons:
            lote.append(som)
            if len(lote) == 512:
                partes.append(self.linhas(np.array(lote))[:, -JANELA:, :].reshape(len(lote), -1))
                lote = []
        if lote:
            partes.append(self.linhas(np.array(lote))[:, -JANELA:, :].reshape(len(lote), -1))
        return np.vstack(partes) if partes else np.zeros((0, JANELA * 96), np.float32)

    def todas_as_janelas(self, som: np.ndarray, passo: int = 1) -> np.ndarray:
        """Um som longo → todas as janelas de 16 linhas, como na escuta de verdade."""
        som = np.concatenate([som, np.zeros(-len(som) % detector.BLOCO, np.float32)])
        linhas = self.linhas(som[None])[0]
        return np.array(
            [linhas[i - JANELA : i].reshape(-1) for i in range(JANELA, len(linhas) + 1, passo)]
        )


# --- 1. Falas sintéticas ------------------------------------------------------------------


def baixar_vozes() -> dict[str, Path]:
    for destino, (url, sha256) in voz_piper.ARQUIVOS.items():
        baixar_se_necessario(url, destino, sha256)
    vozes = {"faber": voz_piper.MODELO}
    for nome, (caminho, hash_modelo, hash_config) in VOZES.items():
        modelo = PASTA_VOZES / f"{nome}.onnx"
        baixar_se_necessario(f"{_BASE}/{caminho}/{nome}.onnx", modelo, hash_modelo)
        baixar_se_necessario(
            f"{_BASE}/{caminho}/{nome}.onnx.json", Path(f"{modelo}.json"), hash_config
        )
        vozes[nome.split("-")[1]] = modelo
    return vozes


def manchetes_de_agora() -> list[str]:
    frases = set()
    for url in FEEDS:
        try:
            pedido = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            raiz = ET.fromstring(urllib.request.urlopen(pedido, timeout=15).read())
        except Exception:  # sem internet ou feed fora do ar: segue com as fixas
            continue
        for item in raiz.iter("item"):
            titulo = re.sub(r"\s+-\s+[^-]+$", "", item.findtext("title") or "").strip()
            if 15 < len(titulo) < 200 and "jarvis" not in titulo.lower():
                frases.add(titulo)
    return sorted(frases)


def gerar_sinteticas() -> None:
    """Escreve os .wav em sinteticas/com e sinteticas/sem (só o que faltar)."""
    from piper import PiperVoice, SynthesisConfig

    com, sem = PASTA_SINTETICAS / "com", PASTA_SINTETICAS / "sem"
    if com.exists() and sem.exists() and any(com.iterdir()):
        return
    com.mkdir(parents=True, exist_ok=True)
    sem.mkdir(parents=True, exist_ok=True)
    falas = SEM_JARVIS + random.sample(manchetes_de_agora() or SEM_JARVIS, 200)
    numero = 0

    def falar(voz, texto: str, pasta: Path, falante: int | None = None) -> None:
        nonlocal numero
        numero += 1
        jeito = SynthesisConfig(
            speaker_id=falante,
            length_scale=rng.uniform(0.8, 1.25),
            noise_scale=rng.uniform(0.5, 0.9),
            noise_w_scale=rng.uniform(0.6, 1.0),
        )
        with wave.open(str(pasta / f"{numero:05d}.wav"), "wb") as arquivo:
            voz.synthesize_wav(texto, arquivo, syn_config=jeito)

    for nome, modelo in baixar_vozes().items():
        print(f"  voz {nome}...", flush=True)
        voz = PiperVoice.load(str(modelo))
        if nome == "libritts_r":
            for falante in random.sample(range(900), 300):
                falar(voz, random.choice(COM_JARVIS_EN), com, falante)
                falar(voz, random.choice(SEM_JARVIS_EN), sem, falante)
            continue
        for _ in range(4):
            for texto in COM_JARVIS:
                falar(voz, texto, com)
        for texto in falas:
            falar(voz, texto, sem)
    if shutil.which("say"):  # vozes do macOS, quando houver
        for voz in VOZES_DO_MACOS:
            for texto in COM_JARVIS[:6]:
                numero += 1
                destino = str(com / f"{numero:05d}.wav")
                comando = ["say", "-v", voz, "-o", destino, "--data-format=LEI16@16000", texto]
                subprocess.run(comando, capture_output=True, check=False)


def caracteristicas_sinteticas(car: Caracteristicas) -> dict[str, np.ndarray]:
    if CACHE_SINTETICOS.exists():
        return dict(np.load(CACHE_SINTETICOS))
    print("1/3 Falas sintéticas (só na primeira vez, ~20 min)...", flush=True)
    gerar_sinteticas()
    com = [normalizar(ler_wav(a)) for a in sorted((PASTA_SINTETICAS / "com").glob("*.wav"))]
    sem = [normalizar(ler_wav(a)) for a in sorted((PASTA_SINTETICAS / "sem").glob("*.wav"))]
    sem = [s for s in sem if len(s) > 1600]
    continuacoes = random.sample(sem, min(300, len(sem)))

    def com_fundo() -> np.ndarray | None:
        return random.choice(sem) if rng.random() < 0.3 else None  # conversa ao fundo

    positivos = (
        encaixar(variar(s, com_fundo()), True, continuacoes) for s in com for _ in range(24)
    )
    negativos = (encaixar(variar(s, com_fundo()), False, []) for s in sem for _ in range(3))
    silencios = (ruido(int(TAXA * DURACAO_S)) * rng.uniform(0, 0.3) for _ in range(300))
    # Fala corrida (como uma TV ligada): as falas emendadas, todas as janelas.
    emendadas = []
    for s in random.sample(sem, len(sem)):
        emendadas += [variar(s), np.zeros(int(TAXA * rng.uniform(0.1, 0.6)), np.float32)]
    corrida = np.concatenate(emendadas)
    blocos = [corrida[i : i + 60 * TAXA] for i in range(0, len(corrida) - 60 * TAXA, 60 * TAXA)]
    dados = {
        "com": car.exemplos(positivos),
        "sem": np.vstack(
            [car.exemplos(negativos), car.exemplos(silencios)]
            + [car.todas_as_janelas(b, passo=2) for b in blocos]
        ),
    }
    PASTA.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE_SINTETICOS, **dados)
    return dados


# --- 2. As suas gravações --------------------------------------------------------------------


def suas_gravacoes() -> list[tuple[np.ndarray, float | None]]:
    """Cada gravação (16 kHz) e onde o "Jarvis" termina nela (None se não tiver o nome)."""
    from faster_whisper import WhisperModel
    from faster_whisper.audio import decode_audio

    from jarvis.habilidades.conversa import transcricao

    whisper = None
    cache = json.loads(CACHE_TRANSCRICOES.read_text()) if CACHE_TRANSCRICOES.exists() else {}
    resultado = []
    for arquivo in sorted(PASTA_GRAVACOES.glob("*")):
        try:
            som = decode_audio(str(arquivo), sampling_rate=TAXA)
        except Exception:  # toque rápido no ESPAÇO: áudio quebrado
            continue
        if len(som) < TAXA // 2:
            continue
        if arquivo.name not in cache:
            whisper = whisper or WhisperModel(
                transcricao.MODELO,
                device="cpu",
                compute_type="int8",
                download_root=str(transcricao.PASTA_MODELOS),
            )
            cache[arquivo.name] = fim_do_jarvis(whisper, arquivo)
        resultado.append((som.astype(np.float32), cache[arquivo.name]))
    PASTA.mkdir(parents=True, exist_ok=True)
    CACHE_TRANSCRICOES.write_text(json.dumps(cache, indent=1))
    return resultado


def fim_do_jarvis(whisper, arquivo: Path) -> float | None:
    """Em que segundo o "Jarvis" termina (o Whisper marca cada palavra)."""
    trechos, _ = whisper.transcribe(
        str(arquivo), language="pt", hotwords="Jarvis", word_timestamps=True, beam_size=5
    )
    for trecho in trechos:
        for palavra in trecho.words or []:
            if re.search(r"j[aá]?r?vi", palavra.word.lower()):
                return round(palavra.end, 2)
    return None


def exemplos_seus(car: Caracteristicas, gravacoes) -> tuple[np.ndarray, np.ndarray]:
    def com_o_nome() -> Iterator[np.ndarray]:
        for som, fim in gravacoes:
            if fim is None:
                continue
            som = som / (np.abs(som).max() + 1e-6)
            for _ in range(60):  # o Whisper erra um pouco o fim da palavra: varia o corte
                corte = min(len(som), int(TAXA * (fim + rng.uniform(-0.05, 0.4))))
                yield encaixar(variar(som[:corte]), True, [])

    def sem_o_nome() -> Iterator[np.ndarray]:
        for som, fim in gravacoes:
            if fim is None:
                som = som / (np.abs(som).max() + 1e-6)
                yield from (encaixar(variar(som), False, []) for _ in range(15))

    return car.exemplos(com_o_nome()), car.exemplos(sem_o_nome())


# --- 3. Treino -----------------------------------------------------------------------------------


def treinar(com: list[np.ndarray], sem: list[np.ndarray]) -> dict[str, np.ndarray]:
    from sklearn.neural_network import MLPClassifier

    x = np.vstack(com + sem)
    y = np.r_[np.ones(sum(len(c) for c in com)), np.zeros(sum(len(s) for s in sem))]
    rede = MLPClassifier(
        hidden_layer_sizes=(64,), alpha=1e-3, max_iter=400, early_stopping=True, random_state=7
    ).fit(x, y)
    return {
        "w1": rede.coefs_[0].astype(np.float32),
        "b1": rede.intercepts_[0].astype(np.float32),
        "w2": rede.coefs_[1].astype(np.float32),
        "b2": rede.intercepts_[1].astype(np.float32),
    }


def notas(pesos: dict[str, np.ndarray], janelas: np.ndarray) -> np.ndarray:
    """A nota de cada janela, já com a regra de "duas notas seguidas"."""
    escondida = np.maximum(0, janelas @ pesos["w1"] + pesos["b1"])
    nota = 1 / (1 + np.exp(-np.clip(escondida @ pesos["w2"] + pesos["b2"], -50, 50)[:, 0]))
    return np.minimum(nota, np.r_[0, nota[:-1]])


def avaliar(car: Caracteristicas, sinteticos, gravacoes) -> None:
    """Treina com metade das suas gravações e testa na outra (e vice-versa)."""
    achou, total, falsos, sem_nome, alarmes, horas = 0, 0, 0, 0, 0, 0.0
    for metade in (0, 1):
        treino = [g for i, g in enumerate(gravacoes) if i % 2 == metade]
        teste = [g for i, g in enumerate(gravacoes) if i % 2 != metade]
        seus_com, seus_sem = exemplos_seus(car, treino)
        pesos = treinar([sinteticos["com"], seus_com], [sinteticos["sem"], seus_sem])
        silencio = np.zeros(TAXA, np.float32)
        for som, fim in teste:
            nota = notas(pesos, car.todas_as_janelas(np.concatenate([silencio, som, silencio])))
            disparou = bool((nota >= detector.LIMIAR).any())
            if fim is None:
                sem_nome += 1
                falsos += disparou
            else:
                total += 1
                achou += disparou
        corrida = np.concatenate([s for s, f in teste if f is None] or [silencio])
        nota = notas(pesos, car.todas_as_janelas(corrida))
        acima = nota >= detector.LIMIAR
        alarmes += int(np.sum(acima[1:] & ~acima[:-1]))
        horas += len(corrida) / TAXA / 3600
    print(f"Seus 'Jarvis' encontrados: {achou} de {total}")
    print(f"Suas falas SEM 'Jarvis' que acordaram o detector: {falsos} de {sem_nome}")
    print(
        f"  (~{alarmes / max(horas, 1e-6):.0f} por hora de fala sua sem o nome; "
        "o Whisper confirma e descarta essas, sem mudar a tela)"
    )


def principal() -> None:
    argumentos = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    argumentos.add_argument("--avaliar", action="store_true", help="só mede, não troca o detector")
    so_avaliar = argumentos.parse_args().avaliar

    car = Caracteristicas()
    sinteticos = caracteristicas_sinteticas(car)
    print("2/3 Suas gravações (o Whisper transcreve as novas)...", flush=True)
    gravacoes = suas_gravacoes()
    com_nome = sum(fim is not None for _, fim in gravacoes)
    print(f"  {len(gravacoes)} gravações, {com_nome} com 'Jarvis'", flush=True)
    if com_nome < 5:
        sys.exit("Poucas gravações com 'Jarvis' (mínimo 5): converse mais com ele e tente de novo.")

    if so_avaliar:
        print("3/3 Avaliando (metade treina, metade testa)...", flush=True)
        avaliar(car, sinteticos, gravacoes)
        return

    print("3/3 Treinando...", flush=True)
    seus_com, seus_sem = exemplos_seus(car, gravacoes)
    pesos = treinar([sinteticos["com"], seus_com], [sinteticos["sem"], seus_sem])
    destino = detector.ARQUIVO_CLASSIFICADOR
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        destino.replace(destino.with_name("jarvis.anterior.npz"))
    np.savez(destino, **pesos)
    print(f"Pronto: {destino}. Reinicie o app para usar o detector novo.")


if __name__ == "__main__":
    principal()
