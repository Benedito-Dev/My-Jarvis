import { describe, expect, it } from "vitest";
import { escolherFormato, estadoDoNucleo } from "./gravacao";

describe("escolherFormato", () => {
  it("prefere o webm quando o sistema suporta (Linux)", () => {
    expect(escolherFormato(() => true)).toBe("audio/webm");
  });

  it("cai no mp4 quando só ele existe (macOS)", () => {
    expect(escolherFormato((tipo) => tipo === "audio/mp4")).toBe("audio/mp4");
  });

  it("devolve null quando o sistema não grava nenhum formato conhecido", () => {
    expect(escolherFormato(() => false)).toBeNull();
  });
});

describe("estadoDoNucleo", () => {
  it("parado, convida a falar", () => {
    expect(estadoDoNucleo({ estado: "parado" })).toMatchObject({
      titulo: "À sua disposição",
      tom: "aviso",
    });
  });

  it("gravando, fica verde e diz que está ouvindo", () => {
    expect(estadoDoNucleo({ estado: "gravando" })).toMatchObject({
      titulo: "Estou ouvindo",
      tom: "ok",
    });
  });

  it("guardada, mostra o arquivo como detalhe", () => {
    const nucleo = estadoDoNucleo({ estado: "guardada", arquivo: "2026-10-17_09-05-03.webm" });

    expect(nucleo.detalhe).toContain("2026-10-17_09-05-03.webm");
    expect(nucleo.tom).toBe("ok");
  });

  it("erro, mostra a mensagem como detalhe", () => {
    expect(estadoDoNucleo({ estado: "erro", mensagem: "Sem microfone" })).toMatchObject({
      detalhe: "Sem microfone",
      tom: "erro",
    });
  });
});
