import { describe, expect, it } from "vitest";
import {
  aplicarEvento,
  duracaoDaFala,
  type EstadoGravacao,
  escolherFormato,
  estadoDoNucleo,
} from "./gravacao";

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

  const ouvida = (texto: string, resposta: string, terminou: boolean): EstadoGravacao => ({
    estado: "ouvida",
    texto,
    resposta,
    acao: null,
    terminou,
  });

  it("ouvida com resposta, volta ao azul e repete o que foi dito", () => {
    const nucleo = estadoDoNucleo(ouvida("que horas são", "São 10 horas.", true));

    expect(nucleo.titulo).toBe("Você disse");
    expect(nucleo.detalhe).toBe("“que horas são”");
    expect(nucleo.tom).toBe("aviso"); // parou de ouvir: volta ao azul
  });

  it("já ouviu mas a resposta não começou: continua roxo, pensando", () => {
    expect(estadoDoNucleo(ouvida("ideia de jantar?", "", false)).tom).toBe("pensando");
  });

  it("ouvida sem texto, avisa que não entendeu", () => {
    expect(estadoDoNucleo(ouvida("", "", true)).titulo).toBe("Não entendi");
  });

  it("erro, mostra a mensagem como detalhe", () => {
    expect(estadoDoNucleo({ estado: "erro", mensagem: "Sem microfone" })).toMatchObject({
      detalhe: "Sem microfone",
      tom: "erro",
    });
  });
});

describe("duracaoDaFala", () => {
  it("frase maior demora mais", () => {
    expect(duracaoDaFala("São 13 horas e 57.")).toBeLessThan(
      duracaoDaFala("Hoje é segunda-feira, 19 de outubro."),
    );
  });

  it("uma frase curta dura uns segundos, não minutos", () => {
    const ms = duracaoDaFala("São 13 horas e 57.");
    expect(ms).toBeGreaterThan(1000);
    expect(ms).toBeLessThan(3000);
  });
});

describe("aplicarEvento", () => {
  it("monta a conversa conforme o fluxo chega", () => {
    let estado: EstadoGravacao = { estado: "enviando" };

    estado = aplicarEvento(estado, { tipo: "ouvido", texto: "jantar?", arquivo: "a.webm" });
    expect(estado).toMatchObject({ estado: "ouvida", texto: "jantar?", resposta: "" });

    estado = aplicarEvento(estado, { tipo: "trecho", texto: "Um omelete." });
    estado = aplicarEvento(estado, { tipo: "trecho", texto: "Fica pronto já." });
    expect(estado).toMatchObject({ resposta: "Um omelete. Fica pronto já.", terminou: false });

    estado = aplicarEvento(estado, { tipo: "fim", acao: "bloquear" });
    expect(estado).toMatchObject({ terminou: true, acao: "bloquear" });
  });

  it("trecho fora de ordem (antes do ouvido) é ignorado", () => {
    const enviando: EstadoGravacao = { estado: "enviando" };

    expect(aplicarEvento(enviando, { tipo: "trecho", texto: "x" })).toBe(enviando);
  });
});
