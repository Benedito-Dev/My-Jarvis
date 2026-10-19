import { describe, expect, it } from "vitest";
import { MEDICOES_LATENCIA, duracaoDesde, guardarLatencia, linhaDoGrafico } from "./modulos";

describe("guardarLatencia", () => {
  it("guarda arredondado e descarta as mais antigas", () => {
    const cheio = Array.from({ length: MEDICOES_LATENCIA }, (_, i) => i);
    const novo = guardarLatencia(cheio, 99.6);

    expect(novo).toHaveLength(MEDICOES_LATENCIA);
    expect(novo[0]).toBe(1);
    expect(novo[novo.length - 1]).toBe(100);
  });
});

describe("duracaoDesde", () => {
  it("formata horas, minutos e segundos", () => {
    const inicio = new Date("2026-10-19T10:00:00Z");
    expect(duracaoDesde(inicio, new Date("2026-10-19T11:02:03Z"))).toBe("01:02:03");
  });

  it("nunca fica negativo", () => {
    const inicio = new Date("2026-10-19T10:00:00Z");
    expect(duracaoDesde(inicio, new Date("2026-10-19T09:59:00Z"))).toBe("00:00:00");
  });
});

describe("linhaDoGrafico", () => {
  it("o maior valor fica no topo e o menor embaixo", () => {
    expect(linhaDoGrafico([2, 10, 6], 100, 20)).toBe("0,20 50,0 100,10");
  });

  it("valores iguais ficam no meio", () => {
    expect(linhaDoGrafico([5, 5], 100, 20)).toBe("0,10 100,10");
  });

  it("sem valores, sem linha", () => {
    expect(linhaDoGrafico([], 100, 20)).toBe("");
  });
});
