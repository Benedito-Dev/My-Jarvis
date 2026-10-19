// Lógica pura da malha do rosto (decisão 0015): levar os pontos que o MediaPipe
// dá, normalizados no quadro da câmera, para o visor redondo da tela — que corta
// o vídeo (object-fit: cover) e o mostra espelhado. Sem canvas nem câmera aqui,
// por isso dá para testar.

export type Ponto = { x: number; y: number };
export type Tamanho = { largura: number; altura: number };
export type Caixa = { esquerda: number; topo: number; direita: number; base: number };

/**
 * Leva um ponto normalizado (0 a 1 no quadro da câmera) para pixels do visor.
 * Faz a mesma conta do `object-fit: cover` (escala até cobrir, centraliza e
 * corta as sobras) e espelha na horizontal, como o vídeo.
 */
export function noVisor(ponto: Ponto, video: Tamanho, visor: Tamanho): Ponto {
  const escala = Math.max(visor.largura / video.largura, visor.altura / video.altura);
  const sobraX = (visor.largura - video.largura * escala) / 2;
  const sobraY = (visor.altura - video.altura * escala) / 2;
  const x = ponto.x * video.largura * escala + sobraX;
  return { x: visor.largura - x, y: ponto.y * video.altura * escala + sobraY };
}

/** A menor caixa que contém todos os pontos. */
export function caixaDosPontos(pontos: Ponto[]): Caixa {
  let esquerda = Infinity;
  let topo = Infinity;
  let direita = -Infinity;
  let base = -Infinity;
  for (const { x, y } of pontos) {
    if (x < esquerda) esquerda = x;
    if (x > direita) direita = x;
    if (y < topo) topo = y;
    if (y > base) base = y;
  }
  return { esquerda, topo, direita, base };
}

/**
 * Suaviza o tremor do detector: cada ponto anda só uma fração (`peso`) do
 * caminho até a posição nova. Mexer pouco fica estável; mexer muito acompanha
 * na hora. Se o número de pontos mudou, não há o que suavizar: usa os novos.
 */
export function suavizar(anteriores: Ponto[] | null, novos: Ponto[], peso: number): Ponto[] {
  if (!anteriores || anteriores.length !== novos.length) return novos;
  return novos.map((novo, i) => {
    const antigo = anteriores[i];
    return { x: antigo.x + (novo.x - antigo.x) * peso, y: antigo.y + (novo.y - antigo.y) * peso };
  });
}
