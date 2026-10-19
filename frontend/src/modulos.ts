// Lógica pura dos módulos laterais do painel (Comando.tsx): histórico de
// latência, tempo de sessão e o desenho do mini-gráfico. Testável sem tela.

/** Quantas medições de latência o gráfico mostra (uma a cada 3 s = 1 minuto). */
export const MEDICOES_LATENCIA = 20;

/** Junta uma medição nova ao histórico, descartando as mais antigas. */
export function guardarLatencia(historico: number[], nova: number): number[] {
  return [...historico, Math.round(nova)].slice(-MEDICOES_LATENCIA);
}

/** Tempo desde `inicio` como "HH:MM:SS". */
export function duracaoDesde(inicio: Date, agora: Date): string {
  const total = Math.max(0, Math.floor((agora.getTime() - inicio.getTime()) / 1000));
  const horas = Math.floor(total / 3600);
  const minutos = Math.floor((total % 3600) / 60);
  const segundos = total % 60;
  return [horas, minutos, segundos].map((n) => String(n).padStart(2, "0")).join(":");
}

/**
 * Os pontos de uma linha (atributo `points` do SVG) que desenha os valores
 * numa caixa `largura` x `altura`. O maior valor encosta no topo; com um só
 * valor, ou todos iguais, a linha fica no meio.
 */
export function linhaDoGrafico(valores: number[], largura: number, altura: number): string {
  if (valores.length === 0) return "";
  const maior = Math.max(...valores);
  const menor = Math.min(...valores);
  const faixa = maior - menor;
  const passo = valores.length > 1 ? largura / (valores.length - 1) : 0;
  return valores
    .map((valor, i) => {
      const y = faixa === 0 ? altura / 2 : altura - ((valor - menor) / faixa) * altura;
      return `${round(i * passo)},${round(y)}`;
    })
    .join(" ");
}

const round = (n: number) => Math.round(n * 10) / 10;
