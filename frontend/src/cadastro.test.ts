import { describe, expect, it } from "vitest";
import { aparencia, nomeInvalido } from "./cadastro";

describe("nomeInvalido", () => {
  it("aceita um nome simples", () => {
    expect(nomeInvalido("benedito")).toBeNull();
  });

  it("aceita números, hífen e sublinhado", () => {
    expect(nomeInvalido("ana_maria-2")).toBeNull();
  });

  it("recusa nome vazio ou só espaços", () => {
    expect(nomeInvalido("   ")).toBe("Digite um nome.");
  });

  it("recusa espaços no meio", () => {
    expect(nomeInvalido("ana maria")).toContain("sem espaços");
  });

  it("recusa acentos, porque vira nome de arquivo", () => {
    expect(nomeInvalido("benedíto")).not.toBeNull();
  });

  it("ignora espaços nas pontas", () => {
    expect(nomeInvalido("  ana  ")).toBeNull();
  });
});

describe("aparencia", () => {
  it("mostra o progresso ao capturar", () => {
    expect(aparencia("capturada", 2, 5).mensagem).toBe(
      "Capturada 2 de 5. Vire o rosto um pouco",
    );
  });

  it("avisa quando tem mais de uma pessoa", () => {
    expect(aparencia("varios_rostos", 0, 5)).toEqual({
      mensagem: "Apenas uma pessoa por vez",
      tom: "aviso",
    });
  });

  it("comemora ao concluir", () => {
    expect(aparencia("concluido", 5, 5).tom).toBe("ok");
  });
});
