import { describe, expect, it } from "vitest";
import { aparencia, escolherFormato } from "./gravacao";

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

describe("aparencia", () => {
  it("convida a falar quando está parado", () => {
    expect(aparencia({ estado: "parado" })).toEqual({
      mensagem: "Segure ESPAÇO para falar",
      tom: "aviso",
    });
  });

  it("avisa que está gravando", () => {
    expect(aparencia({ estado: "gravando" }).tom).toBe("ok");
  });

  it("mostra o arquivo depois de guardar", () => {
    const visual = aparencia({ estado: "guardada", arquivo: "2026-10-17_09-05-03.webm" });

    expect(visual.mensagem).toContain("2026-10-17_09-05-03.webm");
    expect(visual.tom).toBe("ok");
  });

  it("mostra o erro como erro", () => {
    expect(aparencia({ estado: "erro", mensagem: "Sem microfone" })).toEqual({
      mensagem: "Sem microfone",
      tom: "erro",
    });
  });
});
