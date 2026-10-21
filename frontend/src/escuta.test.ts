import { describe, expect, it } from "vitest";
import {
  DURACAO_MAXIMA_S,
  MemoriaDeSom,
  Pedido,
  TAXA_DA_ESCUTA,
  reamostrar,
  volume,
  wav,
} from "./escuta";

const segundos = (s: number, valor = 0) =>
  new Int16Array(Math.round(s * TAXA_DA_ESCUTA)).fill(valor);
const FALA = 8000; // ~0,24 de volume: bem acima do silêncio

describe("reamostrar", () => {
  it("48 kHz vira 16 kHz em 16 bits", () => {
    const entrada = new Float32Array(4800).fill(0.5);

    const saida = reamostrar(entrada, 48000);

    expect(saida.length).toBe(1600);
    expect(saida[0]).toBe(Math.round(0.5 * 32767));
  });

  it("não estoura com som acima do limite", () => {
    expect(reamostrar(new Float32Array(3).fill(2), 48000)[0]).toBe(32767);
  });
});

describe("MemoriaDeSom", () => {
  it("guarda só os últimos segundos", () => {
    const memoria = new MemoriaDeSom(1);
    for (let i = 0; i < 30; i++) memoria.guardar(segundos(0.1, i));

    const tudo = memoria.tudo();

    expect(tudo.length).toBe(TAXA_DA_ESCUTA);
    expect(tudo[tudo.length - 1]).toBe(29); // o mais recente fica no fim
  });
});

describe("Pedido", () => {
  it("acaba depois de fala seguida de silêncio", () => {
    const pedido = new Pedido(segundos(1.5, FALA));

    expect(pedido.juntar(segundos(0.5, FALA))).toBe(false);
    expect(pedido.juntar(segundos(0.5))).toBe(false);
    expect(pedido.juntar(segundos(0.5))).toBe(true);
    expect(pedido.som().length).toBe(3 * TAXA_DA_ESCUTA);
  });

  it("depois do 'Pois não?', espera a pessoa começar a falar", () => {
    const pedido = new Pedido(new Int16Array(0), false);

    expect(pedido.juntar(segundos(2))).toBe(false); // silêncio antes de falar não encerra
    expect(pedido.temFala).toBe(false);
    pedido.juntar(segundos(0.5, FALA));
    expect(pedido.juntar(segundos(1))).toBe(true);
  });

  it("nunca passa da duração máxima", () => {
    const pedido = new Pedido();

    expect(pedido.juntar(segundos(DURACAO_MAXIMA_S, FALA))).toBe(true);
  });
});

describe("volume e wav", () => {
  it("silêncio é zero; fala tem volume", () => {
    expect(volume(segundos(0.1))).toBe(0);
    expect(volume(segundos(0.1, FALA))).toBeCloseTo(FALA / 32768, 3);
  });

  it("monta um wav de 16 kHz, mono, 16 bits", async () => {
    const arquivo = wav(new Int16Array([1, -1, 300]));
    const dados = new DataView(await arquivo.arrayBuffer());

    expect(arquivo.type).toBe("audio/wav");
    expect(arquivo.size).toBe(44 + 6);
    expect(dados.getUint32(24, true)).toBe(16000);
    expect(dados.getInt16(44 + 4, true)).toBe(300);
  });
});
