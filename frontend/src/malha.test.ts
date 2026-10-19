import { describe, expect, it } from "vitest";
import { caixaDosPontos, noVisor, suavizar } from "./malha";

describe("noVisor", () => {
  const visor = { largura: 400, altura: 400 };

  it("centro da câmera cai no centro do visor", () => {
    expect(noVisor({ x: 0.5, y: 0.5 }, { largura: 640, altura: 480 }, visor)).toEqual({
      x: 200,
      y: 200,
    });
  });

  it("espelha: o que está à esquerda da câmera aparece à direita", () => {
    const ponto = noVisor({ x: 0.25, y: 0.5 }, { largura: 400, altura: 400 }, visor);
    expect(ponto.x).toBe(300);
  });

  it("corta as sobras como o object-fit: cover", () => {
    // 640x480 num quadrado de 400: escala 400/480, a largura vira 533 e sobram 66,7 de cada lado.
    const borda = noVisor({ x: 0, y: 0 }, { largura: 640, altura: 480 }, visor);
    expect(borda.y).toBe(0);
    expect(borda.x).toBeCloseTo(400 + 66.67, 1);
  });
});

describe("caixaDosPontos", () => {
  it("envolve todos os pontos", () => {
    expect(
      caixaDosPontos([
        { x: 3, y: 9 },
        { x: 1, y: 4 },
        { x: 7, y: 2 },
      ]),
    ).toEqual({ esquerda: 1, topo: 2, direita: 7, base: 9 });
  });
});

describe("suavizar", () => {
  it("anda só uma fração do caminho", () => {
    expect(suavizar([{ x: 0, y: 0 }], [{ x: 10, y: 20 }], 0.5)).toEqual([{ x: 5, y: 10 }]);
  });

  it("sem histórico usa os pontos novos", () => {
    const novos = [{ x: 1, y: 1 }];
    expect(suavizar(null, novos, 0.5)).toBe(novos);
  });
});
