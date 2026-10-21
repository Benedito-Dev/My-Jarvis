// Os cartões da conversa: o que uma ferramenta do Jarvis trouxe (clima,
// lembretes, pesquisa...), organizado para a tela. Chegam do backend no fluxo
// da conversa (evento "cartao"). Aqui fica só a lógica pura, testável.

type Base = { rotulo: string; titulo: string };

export type DiaDoClima = {
  nome: string;
  ceu: string;
  maxima: number;
  minima: number;
  /** Chance de chuva em %, ou null quando a previsão não diz. */
  chuva: number | null;
};

export type Cartao = Base &
  (
    | {
        tipo: "clima";
        temperatura: number;
        sensacao: number;
        umidade: number;
        ceu: string;
        dias: DiaDoClima[];
      }
    | { tipo: "lembretes"; itens: { hora: string; texto: string }[] }
    | { tipo: "pesquisa"; itens: { titulo: string; resumo: string; fonte: string }[] }
    | { tipo: "noticia"; fonte: string; imagem: string | null }
    | { tipo: "notas"; itens: string[] }
    | { tipo: "conta"; expressao: string }
    | { tipo: "abrir" }
  );

// O que aparece enquanto a ferramenta roda (o nome é o do backend, ferramentas.py).
const EM_USO: Record<string, string> = {
  clima: "Consultando o clima",
  pesquisar_web: "Pesquisando na web",
  criar_lembrete: "Agendando o lembrete",
  listar_lembretes: "Lendo seus lembretes",
  anotar: "Anotando",
  ler_notas: "Lendo suas notas",
  calcular: "Calculando",
  noticias: "Lendo as notícias",
  abrir_app: "Abrindo o app",
  abrir_site: "Abrindo o site",
};

/** "Consultando o clima": o que o Jarvis está fazendo com a ferramenta `nome`. */
export function fraseDaFerramenta(nome: string): string {
  return EM_USO[nome] ?? "Trabalhando nisso";
}

/**
 * Os cartões desta conversa cuja fala já começou a tocar. `falaDoCartao[i]` é
 * quantos trechos vieram antes do cartão i; `falasTocadas` é quantas falas da
 * conversa já começaram (null quando o backend não avisa: aí, todos).
 * No bom dia, o cartão do clima sobe com a fala do clima, o das notícias com a das notícias.
 */
export function cartoesJaFalados(
  cartoes: Cartao[],
  falaDoCartao: number[],
  falasTocadas: number | null,
): Cartao[] {
  if (falasTocadas === null) return cartoes;
  return cartoes.filter((_, i) => (falaDoCartao[i] ?? 0) < falasTocadas);
}

/** Quantos cartões cabem na fileira de baixo. */
export const CARTOES_NA_FILA = 4;

/**
 * O que a tela mostra: o cartão em destaque (na frente do orbe) e a fileira de
 * baixo. Os cartões desta conversa esperam escondidos enquanto ele trabalha e só
 * aparecem quando a voz começa: o último em destaque, os outros na fileira.
 * Quando ele volta a esperar, todos descem para a fileira.
 */
export function arrumarCartoes(
  anteriores: Cartao[],
  atuais: Cartao[],
  momento: "trabalhando" | "falando" | "espera",
): { destaque: Cartao | null; fila: Cartao[] } {
  if (momento === "espera" || atuais.length === 0) {
    return { destaque: null, fila: [...anteriores, ...atuais].slice(-CARTOES_NA_FILA) };
  }
  if (momento === "trabalhando") {
    return { destaque: null, fila: anteriores.slice(-CARTOES_NA_FILA) };
  }
  return {
    destaque: atuais[atuais.length - 1],
    fila: [...anteriores, ...atuais.slice(0, -1)].slice(-CARTOES_NA_FILA),
  };
}

/** O valor que resume o cartão na fileira: "24°", "2 lembretes", "591.6"... */
export function resumoDoCartao(cartao: Cartao): string {
  switch (cartao.tipo) {
    case "clima":
      return `${cartao.temperatura}° · ${cartao.ceu}`;
    case "pesquisa":
      return cartao.itens[0]?.titulo ?? cartao.titulo;
    case "notas":
      return cartao.itens[cartao.itens.length - 1] ?? cartao.titulo;
    case "lembretes":
      return cartao.itens.length === 1
        ? `${cartao.itens[0].hora} · ${cartao.itens[0].texto}`
        : cartao.titulo;
    default:
      return cartao.titulo;
  }
}
