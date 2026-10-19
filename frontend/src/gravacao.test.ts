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

  it("enviando, fica roxo e diz que está pensando", () => {
    expect(estadoDoNucleo({ estado: "enviando" })).toMatchObject({
      titulo: "Pensando",
      tom: "pensando",
    });
  });

  it("ouvida, volta ao azul e repete o que foi dito", () => {
    const nucleo = estadoDoNucleo({ estado: "ouvida", texto: "que horas são" });

    expect(nucleo.titulo).toBe("Você disse");
    expect(nucleo.detalhe).toBe("“que horas são”");
    expect(nucleo.tom).toBe("aviso"); // parou de ouvir: volta ao azul
  });

  it("ouvida sem texto, avisa que não entendeu", () => {
    expect(estadoDoNucleo({ estado: "ouvida", texto: "" }).titulo).toBe("Não entendi");
  });

  it("erro, mostra a mensagem como detalhe", () => {
    expect(estadoDoNucleo({ estado: "erro", mensagem: "Sem microfone" })).toMatchObject({
      detalhe: "Sem microfone",
      tom: "erro",
    });
  });
});
