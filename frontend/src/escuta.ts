// A escuta sem tecla: lógica pura (testável) para o som do microfone.
// O app manda o som em 16 kHz para o backend, que diz quando ouviu "Jarvis"
// (decisão 0023). Aqui ficam a conversão do som, a memória dos últimos
// instantes (o "Jarvis" já foi dito quando o aviso chega) e o fim da fala.

export const TAXA_DA_ESCUTA = 16000;

/** Quanto som "para trás" entra na gravação: o "Jarvis" e um respiro antes. */
export const SEGUNDOS_ANTES = 1.5;
/** Silêncio que encerra o pedido. */
export const SILENCIO_QUE_ENCERRA_S = 0.9;
/** Nenhum pedido passa disto (alguém conversando perto não grava para sempre). */
export const DURACAO_MAXIMA_S = 12;
/** Volume (RMS, de 0 a 1) abaixo do qual o pedaço conta como silêncio. */
export const VOLUME_DE_SILENCIO = 0.015;

/** Som do microfone (float, de -1 a 1, na taxa do sistema) → 16 kHz em 16 bits. */
export function reamostrar(entrada: Float32Array, taxaDeEntrada: number): Int16Array<ArrayBuffer> {
  const passo = taxaDeEntrada / TAXA_DA_ESCUTA;
  const saida = new Int16Array(Math.floor(entrada.length / passo));
  for (let i = 0; i < saida.length; i++) {
    // Média das amostras que caem neste ponto: evita o chiado de só pular amostras.
    const inicio = Math.floor(i * passo);
    const fim = Math.max(inicio + 1, Math.floor((i + 1) * passo));
    let soma = 0;
    for (let j = inicio; j < fim; j++) soma += entrada[j];
    const valor = Math.max(-1, Math.min(1, soma / (fim - inicio)));
    saida[i] = Math.round(valor * 32767);
  }
  return saida;
}

/** Volume do pedaço (RMS), de 0 a 1. */
export function volume(pcm: Int16Array): number {
  if (pcm.length === 0) return 0;
  let soma = 0;
  for (const amostra of pcm) soma += (amostra / 32768) ** 2;
  return Math.sqrt(soma / pcm.length);
}

/** Guarda só os últimos `segundos` de som: o que veio antes do "Jarvis". */
export class MemoriaDeSom {
  private pedacos: Int16Array[] = [];
  private total = 0;
  private readonly maximo: number;

  constructor(segundos = SEGUNDOS_ANTES) {
    this.maximo = Math.round(segundos * TAXA_DA_ESCUTA);
  }

  guardar(pcm: Int16Array): void {
    this.pedacos.push(pcm);
    this.total += pcm.length;
    while (this.pedacos.length > 1 && this.total - this.pedacos[0].length >= this.maximo) {
      this.total -= this.pedacos.shift()!.length;
    }
  }

  /** O som guardado, numa peça só (no máximo `segundos`). */
  tudo(): Int16Array {
    const junto = juntar(this.pedacos);
    return junto.subarray(Math.max(0, junto.length - this.maximo));
  }

  esvaziar(): void {
    this.pedacos = [];
    this.total = 0;
  }
}

/**
 * Grava o pedido até a pessoa parar de falar: depois de ter havido fala,
 * `SILENCIO_QUE_ENCERRA_S` de silêncio encerra; e nunca passa de `DURACAO_MAXIMA_S`.
 */
export class Pedido {
  private pedacos: Int16Array[];
  private amostras: number;
  private silencio = 0;
  private falou: boolean;

  constructor(antes: Int16Array = new Int16Array(0), jaFalou = true) {
    this.pedacos = [antes];
    this.amostras = antes.length;
    // Acordado pelo "Jarvis", a fala já começou; depois do "Pois não?", ainda não.
    this.falou = jaFalou;
  }

  /** Junta o pedaço; devolve true quando o pedido acabou. */
  juntar(pcm: Int16Array): boolean {
    this.pedacos.push(pcm);
    this.amostras += pcm.length;
    if (volume(pcm) < VOLUME_DE_SILENCIO) {
      this.silencio += pcm.length;
    } else {
      this.silencio = 0;
      this.falou = true;
    }
    const segundos = (n: number) => n / TAXA_DA_ESCUTA;
    return (
      (this.falou && segundos(this.silencio) >= SILENCIO_QUE_ENCERRA_S) ||
      segundos(this.amostras) >= DURACAO_MAXIMA_S
    );
  }

  /** Alguém falou de fato (senão nem vale mandar). */
  get temFala(): boolean {
    return this.falou;
  }

  som(): Int16Array {
    return juntar(this.pedacos);
  }
}

/** O som num arquivo .wav (o backend aceita wav, ver gravacoes.py). */
export function wav(pcm: Int16Array, taxa = TAXA_DA_ESCUTA): Blob {
  const cabecalho = new DataView(new ArrayBuffer(44));
  const texto = (posicao: number, valor: string) =>
    [...valor].forEach((letra, i) => cabecalho.setUint8(posicao + i, letra.charCodeAt(0)));
  texto(0, "RIFF");
  cabecalho.setUint32(4, 36 + pcm.length * 2, true);
  texto(8, "WAVE");
  texto(12, "fmt ");
  cabecalho.setUint32(16, 16, true); // tamanho do bloco "fmt"
  cabecalho.setUint16(20, 1, true); // PCM
  cabecalho.setUint16(22, 1, true); // mono
  cabecalho.setUint32(24, taxa, true);
  cabecalho.setUint32(28, taxa * 2, true); // bytes por segundo
  cabecalho.setUint16(32, 2, true); // bytes por amostra
  cabecalho.setUint16(34, 16, true); // bits por amostra
  texto(36, "data");
  cabecalho.setUint32(40, pcm.length * 2, true);
  // O WAV é little-endian, como os processadores onde o app roda.
  const corpo = new Uint8Array(pcm.buffer, pcm.byteOffset, pcm.byteLength).slice();
  return new Blob([cabecalho.buffer, corpo], { type: "audio/wav" });
}

function juntar(pedacos: Int16Array[]): Int16Array {
  const total = pedacos.reduce((soma, p) => soma + p.length, 0);
  const junto = new Int16Array(total);
  let posicao = 0;
  for (const pedaco of pedacos) {
    junto.set(pedaco, posicao);
    posicao += pedaco.length;
  }
  return junto;
}
