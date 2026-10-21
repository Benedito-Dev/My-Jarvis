import { describe, expect, it } from "vitest";
import {
  aplicarEvento,
  faseDoPainel,
  registrarTroca,
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
    cartoes: [],
    usando: null,
    trechos: 0,
    falaDoCartao: [],
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

  it("ferramenta em uso e depois o cartão que ela trouxe", () => {
    const cartao = { tipo: "abrir" as const, rotulo: "Abrindo app", titulo: "Spotify" };
    let estado = aplicarEvento({ estado: "enviando" }, { tipo: "ouvido", texto: "abre", arquivo: "" });
    estado = aplicarEvento(estado, { tipo: "usando", ferramenta: "abrir_app" });
    expect(estado).toMatchObject({ usando: "abrir_app", cartoes: [] });

    estado = aplicarEvento(estado, { tipo: "cartao", cartao });
    expect(estado).toMatchObject({ usando: null, cartoes: [cartao] });
  });

  it("cada cartão guarda quantos trechos vieram antes dele", () => {
    const cartao = { tipo: "abrir" as const, rotulo: "Abrindo app", titulo: "Spotify" };
    let estado = aplicarEvento({ estado: "enviando" }, { tipo: "ouvido", texto: "bom dia", arquivo: "" });
    estado = aplicarEvento(estado, { tipo: "trecho", texto: "Bom dia, Benedito." });
    estado = aplicarEvento(estado, { tipo: "cartao", cartao });
    estado = aplicarEvento(estado, { tipo: "trecho", texto: "Em Fortaleza..." });
    estado = aplicarEvento(estado, { tipo: "cartao", cartao });

    expect(estado).toMatchObject({ trechos: 2, falaDoCartao: [1, 2] });
  });
});

describe("faseDoPainel", () => {
  const conversa = (terminou: boolean): EstadoGravacao => ({
    estado: "ouvida",
    texto: "e o clima?",
    resposta: "Faz 30 graus.",
    acao: null,
    terminou,
    cartoes: [],
    usando: null,
    trechos: 0,
    falaDoCartao: [],
  });

  it("a pausa entre frases não vira espera enquanto a resposta não terminou", () => {
    expect(faseDoPainel(conversa(false), false)).toBe("pensando");
    expect(faseDoPainel(conversa(false), true)).toBe("falando");
  });

  it("terminou e parou de falar: em espera", () => {
    expect(faseDoPainel(conversa(true), false)).toBe("espera");
    expect(faseDoPainel({ estado: "parado" }, false)).toBe("espera");
  });

  it("resposta pronta mas a voz ainda não começou: segue pensando", () => {
    expect(faseDoPainel(conversa(true), false, true)).toBe("pensando");
  });

  it("gravando é sempre ouvindo", () => {
    expect(faseDoPainel({ estado: "gravando" }, true)).toBe("ouvindo");
  });
});

describe("registrarTroca", () => {
  const quando = new Date("2026-10-20T11:00:00Z");
  const terminada: EstadoGravacao = {
    estado: "ouvida",
    texto: "que horas são",
    resposta: "São 11 horas.",
    acao: null,
    terminou: true,
    cartoes: [],
    usando: null,
    trechos: 0,
    falaDoCartao: [],
  };

  it("guarda a troca quando a conversa termina", () => {
    expect(registrarTroca([], terminada, quando)).toEqual([
      { id: 1, pergunta: "que horas são", resposta: "São 11 horas.", quando },
    ]);
  });

  it("não guarda conversa pela metade nem fala vazia", () => {
    expect(registrarTroca([], { ...terminada, terminou: false }, quando)).toEqual([]);
    expect(registrarTroca([], { ...terminada, texto: "" }, quando)).toEqual([]);
  });

  it("guarda só as mais recentes", () => {
    let historico = registrarTroca([], terminada, quando);
    historico = registrarTroca(historico, terminada, quando, 1);

    expect(historico.map((t) => t.id)).toEqual([2]);
  });
});
