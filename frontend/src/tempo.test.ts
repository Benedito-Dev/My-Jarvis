import { describe, expect, it } from "vitest";
import {
  cumprimento,
  formatarData,
  formatarHora,
  formatarHoraCompleta,
  horaNoFuso,
} from "./tempo";

// Horários em UTC; São Paulo é UTC-3.
const emSaoPaulo = (horaLocal: number) =>
  new Date(Date.UTC(2026, 9, 16, horaLocal + 3, 30));

describe("cumprimento", () => {
  it.each([
    [5, "Bom dia"],
    [11, "Bom dia"],
    [12, "Boa tarde"],
    [17, "Boa tarde"],
    [18, "Boa noite"],
    [20, "Boa noite"],
  ])("às %ih em São Paulo diz '%s'", (hora, esperado) => {
    expect(cumprimento(emSaoPaulo(hora))).toBe(esperado);
  });

  it("de madrugada diz 'Boa noite'", () => {
    expect(cumprimento(new Date(Date.UTC(2026, 9, 16, 5, 0)))).toBe("Boa noite"); // 2h em SP
  });
});

describe("fuso", () => {
  it("usa o horário de São Paulo, não o da máquina", () => {
    expect(horaNoFuso(new Date(Date.UTC(2026, 9, 16, 12, 0)))).toBe(9);
  });

  it("formata data e hora em português", () => {
    const data = emSaoPaulo(16);
    expect(formatarData(data)).toBe("sexta-feira, 16 de outubro");
    expect(formatarHora(data)).toBe("16:30");
  });
});

describe("formatarHoraCompleta", () => {
  it("mostra hora, minuto e segundo no fuso do Brasil", () => {
    // 2026-10-17T23:45:03Z = 20:45:03 em São Paulo (UTC-3)
    expect(formatarHoraCompleta(new Date("2026-10-17T23:45:03Z"))).toBe("20:45:03");
  });
});
