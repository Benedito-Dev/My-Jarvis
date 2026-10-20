import { describe, expect, it } from "vitest";
import { nivelNoInstante } from "./voz";

describe("nivelNoInstante", () => {
  const envelope = [0.1, 0.8, 0.4];

  it("acompanha o envelope pelo tempo", () => {
    expect(nivelNoInstante(envelope, 40, 0)).toBe(0.1);
    expect(nivelNoInstante(envelope, 40, 50)).toBe(0.8);
    expect(nivelNoInstante(envelope, 40, 119)).toBe(0.4);
  });

  it("antes de começar e depois de acabar é silêncio", () => {
    expect(nivelNoInstante(envelope, 40, -5)).toBe(0);
    expect(nivelNoInstante(envelope, 40, 120)).toBe(0);
  });
});
