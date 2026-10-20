import { describe, expect, it } from "vitest";
import { criarFios, girar, nivelDoSinal, pontoDoFio } from "./nucleo";

describe("girar", () => {
  it("meia volta em Y leva a frente para trás", () => {
    const { x, y, z } = girar({ x: 0, y: 0, z: 1 }, Math.PI, 0);
    expect(x).toBeCloseTo(0, 6);
    expect(y).toBeCloseTo(0, 6);
    expect(z).toBeCloseTo(-1, 6);
  });
});

describe("nivelDoSinal", () => {
  it("silêncio é zero", () => {
    expect(nivelDoSinal(new Uint8Array(64).fill(128))).toBe(0);
  });

  it("som alto satura em 1", () => {
    const alto = Uint8Array.from({ length: 64 }, (_, i) => (i % 2 ? 255 : 0));
    expect(nivelDoSinal(alto)).toBe(1);
  });

  it("ruído de fundo fica em zero", () => {
    const ruido = Uint8Array.from({ length: 64 }, (_, i) => (i % 2 ? 129 : 127));
    expect(nivelDoSinal(ruido)).toBe(0);
  });

  it("fala baixa já fica no meio da escala", () => {
    const baixo = Uint8Array.from({ length: 64 }, (_, i) => (i % 2 ? 134 : 122));
    const nivel = nivelDoSinal(baixo);
    expect(nivel).toBeGreaterThan(0.3);
    expect(nivel).toBeLessThan(1);
  });
});

describe("fios do orbe", () => {
  const fios = criarFios(12);

  it("são sempre os mesmos (sem sorteio)", () => {
    expect(criarFios(12)).toEqual(fios);
  });

  it("cada fio é um laço fechado", () => {
    for (const fio of fios) {
      const inicio = pontoDoFio(fio, 0, 3.2, 0.5);
      const fim = pontoDoFio(fio, Math.PI * 2, 3.2, 0.5);
      expect(fim.x).toBeCloseTo(inicio.x, 6);
      expect(fim.y).toBeCloseTo(inicio.y, 6);
      expect(fim.z).toBeCloseTo(inicio.z, 6);
    }
  });

  it("em silêncio fica perto da esfera, e a voz abre o orbe", () => {
    const maiorDistancia = (energia: number) =>
      Math.max(
        ...fios.flatMap((fio) =>
          Array.from({ length: 64 }, (_, i) => {
            const p = pontoDoFio(fio, (i / 64) * Math.PI * 2, 1, energia);
            return Math.hypot(p.x, p.y, p.z);
          }),
        ),
      );
    expect(maiorDistancia(0)).toBeLessThan(1.15);
    expect(maiorDistancia(1)).toBeGreaterThan(maiorDistancia(0));
  });
});
