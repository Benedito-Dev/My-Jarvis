// Lógica pura do núcleo do painel: os pontos da esfera e o volume da voz.
// Sem canvas nem microfone aqui, por isso dá para testar.

export type Ponto3D = { x: number; y: number; z: number };

/**
 * `quantidade` pontos espalhados por igual numa esfera de raio 1 (espiral de
 * Fibonacci). Distribuição uniforme sem sorteio: a esfera é sempre a mesma.
 */
export function pontosNaEsfera(quantidade: number): Ponto3D[] {
  const anguloDourado = Math.PI * (3 - Math.sqrt(5));
  return Array.from({ length: quantidade }, (_, i) => {
    const y = quantidade === 1 ? 0 : 1 - (i / (quantidade - 1)) * 2;
    const raio = Math.sqrt(1 - y * y);
    const angulo = anguloDourado * i;
    return { x: Math.cos(angulo) * raio, y, z: Math.sin(angulo) * raio };
  });
}

/** Gira um ponto em volta do eixo Y e depois do eixo X (ângulos em radianos). */
export function girar(ponto: Ponto3D, emY: number, emX: number): Ponto3D {
  const x = ponto.x * Math.cos(emY) + ponto.z * Math.sin(emY);
  const z1 = -ponto.x * Math.sin(emY) + ponto.z * Math.cos(emY);
  const y = ponto.y * Math.cos(emX) - z1 * Math.sin(emX);
  const z = ponto.y * Math.sin(emX) + z1 * Math.cos(emX);
  return { x, y, z };
}

// Abaixo disto é ruído de fundo do microfone, não voz.
const PISO_DE_RUIDO = 0.008;
// Ganho depois do piso. A raiz quadrada no fim abre a escala das falas baixas:
// fala normal (RMS ~0,03-0,1) cai entre 0,4 e 0,9, em vez de quase zero.
const GANHO_VOZ = 8;

/**
 * Volume de 0 a 1 de um trecho de áudio no formato do `getByteTimeDomainData`
 * (bytes de 0 a 255, com o silêncio em 128).
 */
export function nivelDoSinal(amostras: Uint8Array): number {
  if (amostras.length === 0) return 0;
  let soma = 0;
  for (const amostra of amostras) {
    const desvio = (amostra - 128) / 128;
    soma += desvio * desvio;
  }
  const rms = Math.sqrt(soma / amostras.length);
  return Math.min(1, Math.sqrt(Math.max(0, rms - PISO_DE_RUIDO) * GANHO_VOZ));
}
