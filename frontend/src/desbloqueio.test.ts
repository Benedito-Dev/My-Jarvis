import { describe, expect, it } from "vitest";
import { aparencia } from "./desbloqueio";

describe("aparencia", () => {
  it("pede para aproximar quando não vê rosto ou está longe", () => {
    expect(aparencia("sem_rosto", null)).toEqual({
      mensagem: "Por favor, aproxime seu rosto",
      tom: "aviso",
    });
    expect(aparencia("longe", null).mensagem).toBe("Por favor, aproxime seu rosto");
  });

  it("nega acesso a desconhecidos em vermelho", () => {
    expect(aparencia("desconhecido", null)).toEqual({ mensagem: "Acesso negado", tom: "erro" });
  });

  it("dá boas-vindas pelo nome", () => {
    expect(aparencia("desbloqueado", "Benedito")).toEqual({
      mensagem: "Bem-vindo, Benedito",
      tom: "ok",
    });
  });
});
