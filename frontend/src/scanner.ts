import type { Ponto, Retangulo } from "./api";

/** Oval que aproxima o rosto: centro, raios e quantos graus está inclinado. */
export type Contorno = { cx: number; cy: number; rx: number; ry: number; giro: number };

// O YuNet entrega uma caixa mais larga que o rosto (sobra fundo dos dois lados),
// então o oval é mais estreito que ela. A altura aproveita a caixa inteira:
// ela vai do alto da testa ao queixo.
const FRACAO_DA_LARGURA = 0.44;

/**
 * Molda o scanner no rosto: um oval inscrito na caixa do detector, girado junto
 * com os olhos. Com 5 pontos não há como traçar o contorno real (isso pediria um
 * modelo de 68 pontos), mas o oval inclinado já acompanha a cabeça virando.
 */
export function contorno(rosto: Retangulo): Contorno {
  const largura = rosto.direita - rosto.esquerda;
  const altura = rosto.base - rosto.topo;
  return {
    cx: rosto.esquerda + largura / 2,
    cy: rosto.topo + altura / 2,
    rx: largura * FRACAO_DA_LARGURA,
    ry: altura / 2,
    giro: inclinacao(rosto.pontos),
  };
}

/** Inclinação dos olhos em graus. Zero se o rosto veio sem os pontos. */
export function inclinacao(pontos: Ponto[]): number {
  const por_nome = new Map(pontos.map((ponto) => [ponto.nome, ponto]));
  const direito = por_nome.get("olho_direito");
  const esquerdo = por_nome.get("olho_esquerdo");
  if (!direito || !esquerdo) return 0;
  return (Math.atan2(esquerdo.y - direito.y, esquerdo.x - direito.x) * 180) / Math.PI;
}
