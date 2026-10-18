import { describe, expect, it } from "vitest";
import type { Ponto, Retangulo } from "./api";
import { contorno, inclinacao } from "./scanner";

const PONTOS: Ponto[] = [
  { nome: "olho_direito", x: 40, y: 50 },
  { nome: "olho_esquerdo", x: 80, y: 50 },
  { nome: "nariz", x: 60, y: 70 },
  { nome: "boca_direita", x: 45, y: 90 },
  { nome: "boca_esquerda", x: 75, y: 90 },
];

const ROSTO: Retangulo = { topo: 0, direita: 100, base: 200, esquerda: 0, pontos: PONTOS };

describe("contorno", () => {
  it("centra o oval no rosto", () => {
    expect(contorno(ROSTO)).toMatchObject({ cx: 50, cy: 100 });
  });

  it("usa a altura inteira da caixa e estreita a largura", () => {
    expect(contorno(ROSTO)).toMatchObject({ rx: 44, ry: 100 });
  });

  it("gira junto com os olhos", () => {
    const inclinado = { ...ROSTO, pontos: PONTOS.map((p) => ({ ...p, y: p.x })) };

    expect(contorno(inclinado).giro).toBeCloseTo(45);
  });
});

describe("inclinacao", () => {
  it("é zero com os olhos na mesma altura", () => {
    expect(inclinacao(PONTOS)).toBe(0);
  });

  it("é negativa com a cabeça tombada para um lado", () => {
    const tombado = PONTOS.map((p) => (p.nome === "olho_esquerdo" ? { ...p, y: 10 } : p));

    expect(inclinacao(tombado)).toBeLessThan(0);
  });

  it("é zero sem pontos, sem quebrar", () => {
    expect(inclinacao([])).toBe(0);
  });
});
