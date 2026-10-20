import { describe, expect, it } from "vitest";
import { LeitorDeLinhas } from "./linhas";

describe("LeitorDeLinhas", () => {
  it("guarda o pedaço de linha até ela fechar", () => {
    const leitor = new LeitorDeLinhas();

    expect(leitor.empurrar('{"tipo": "ouv')).toEqual([]);
    expect(leitor.empurrar('ido"}\n{"tipo"')).toEqual(['{"tipo": "ouvido"}']);
    expect(leitor.empurrar(': "fim"}\n')).toEqual(['{"tipo": "fim"}']);
  });

  it("várias linhas num pedaço só", () => {
    expect(new LeitorDeLinhas().empurrar("a\nb\n\nc\n")).toEqual(["a", "b", "c"]);
  });

  it("entrega o que sobrou sem quebra de linha no fim", () => {
    const leitor = new LeitorDeLinhas();
    leitor.empurrar("ultima");

    expect(leitor.terminar()).toEqual(["ultima"]);
  });
});
