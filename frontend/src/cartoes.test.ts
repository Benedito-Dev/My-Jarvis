import { describe, expect, it } from "vitest";
import {
  type Cartao,
  arrumarCartoes,
  cartoesJaFalados,
  fraseDaFerramenta,
  resumoDoCartao,
} from "./cartoes";

const cartao = (titulo: string): Cartao => ({ tipo: "abrir", rotulo: "Abrindo app", titulo });

describe("arrumarCartoes", () => {
  const anteriores = [cartao("a"), cartao("b")];

  it("falando, o último cartão da conversa fica em destaque", () => {
    const { destaque, fila } = arrumarCartoes(anteriores, [cartao("c"), cartao("d")], "falando");

    expect(destaque?.titulo).toBe("d");
    expect(fila.map((c) => c.titulo)).toEqual(["a", "b", "c"]);
  });

  it("em espera, todos descem para a fileira", () => {
    const { destaque, fila } = arrumarCartoes(anteriores, [cartao("c")], "espera");

    expect(destaque).toBeNull();
    expect(fila.map((c) => c.titulo)).toEqual(["a", "b", "c"]);
  });

  it("trabalhando, os desta conversa esperam escondidos até ele falar", () => {
    const { destaque, fila } = arrumarCartoes(anteriores, [cartao("c")], "trabalhando");

    expect(destaque).toBeNull();
    expect(fila.map((c) => c.titulo)).toEqual(["a", "b"]);
  });

  it("a fileira guarda só os mais recentes", () => {
    const muitos = ["1", "2", "3", "4", "5", "6"].map(cartao);

    expect(arrumarCartoes(muitos, [], "espera").fila.map((c) => c.titulo)).toEqual([
      "3",
      "4",
      "5",
      "6",
    ]);
  });
});

describe("fraseDaFerramenta", () => {
  it("diz o que está fazendo, mesmo com ferramenta desconhecida", () => {
    expect(fraseDaFerramenta("clima")).toBe("Consultando o clima");
    expect(fraseDaFerramenta("nova_coisa")).toBe("Trabalhando nisso");
  });
});

describe("resumoDoCartao", () => {
  it("clima mostra a temperatura e o céu", () => {
    const clima: Cartao = {
      tipo: "clima",
      rotulo: "Clima · agora",
      titulo: "Fortaleza",
      temperatura: 31,
      sensacao: 34,
      umidade: 50,
      ceu: "céu limpo",
      dias: [],
    };
    expect(resumoDoCartao(clima)).toBe("31° · céu limpo");
  });

  it("um lembrete só mostra a hora e o texto", () => {
    const lembrete: Cartao = {
      tipo: "lembretes",
      rotulo: "Lembrete criado",
      titulo: "1 lembrete",
      itens: [{ hora: "15:00", texto: "ligar pro banco" }],
    };
    expect(resumoDoCartao(lembrete)).toBe("15:00 · ligar pro banco");
  });
});

describe("cartoesJaFalados", () => {
  const tres = [cartao("clima"), cartao("lembretes"), cartao("noticias")];
  // Bom dia: cumprimento (fala 0), depois cada cartão antes da sua fala.
  const falaDoCartao = [1, 2, 3];

  it("mostra cada cartão só quando a fala dele começa", () => {
    expect(cartoesJaFalados(tres, falaDoCartao, 1)).toEqual([]);
    expect(cartoesJaFalados(tres, falaDoCartao, 2).map((c) => c.titulo)).toEqual(["clima"]);
    expect(cartoesJaFalados(tres, falaDoCartao, 4)).toHaveLength(3);
  });

  it("sem aviso das falas (sem voz), mostra todos", () => {
    expect(cartoesJaFalados(tres, falaDoCartao, null)).toHaveLength(3);
  });
});
