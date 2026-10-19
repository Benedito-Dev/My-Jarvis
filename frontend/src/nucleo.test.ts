import { describe, expect, it } from "vitest";
import { girar, nivelDoSinal, pontosNaEsfera } from "./nucleo";

describe("pontosNaEsfera", () => {
  it("todos os pontos ficam na superfície da esfera", () => {
    for (const { x, y, z } of pontosNaEsfera(200)) {
      expect(Math.hypot(x, y, z)).toBeCloseTo(1, 6);
    }
  });

  it("vai de um polo ao outro", () => {
    const pontos = pontosNaEsfera(50);
    expect(pontos[0].y).toBe(1);
    expect(pontos[49].y).toBe(-1);
  });
});

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
