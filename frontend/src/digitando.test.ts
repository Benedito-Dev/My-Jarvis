import { describe, expect, it } from "vitest";
import { trechoDigitado } from "./digitando";

describe("trechoDigitado", () => {
  it("vai revelando uma letra por vez", () => {
    expect(trechoDigitado("olá", 0, 30)).toBe("");
    expect(trechoDigitado("olá", 65, 30)).toBe("ol");
  });

  it("para no fim do texto", () => {
    expect(trechoDigitado("olá", 10_000, 30)).toBe("olá");
  });
});
