// Lógica pura do núcleo do painel: os fios de luz do orbe e o volume da voz.
// Sem canvas nem microfone aqui, por isso dá para testar.

export type Ponto3D = { x: number; y: number; z: number };

/** Gira um ponto em volta do eixo Y e depois do eixo X (ângulos em radianos). */
export function girar(ponto: Ponto3D, emY: number, emX: number): Ponto3D {
  const x = ponto.x * Math.cos(emY) + ponto.z * Math.sin(emY);
  const z1 = -ponto.x * Math.sin(emY) + ponto.z * Math.cos(emY);
  const y = ponto.y * Math.cos(emX) - z1 * Math.sin(emX);
  const z = ponto.y * Math.sin(emX) + z1 * Math.cos(emX);
  return { x, y, z };
}

/**
 * Um fio de luz do orbe: um laço fechado em volta do centro, num plano
 * inclinado (eixos `u` e `v`, normal `n`). O raio ondula com algumas
 * harmônicas, e o laço sobe e desce para fora do plano: por isso os fios
 * se cruzam como um novelo, em vez de serem círculos certinhos.
 */
export type Fio = {
  u: Ponto3D;
  v: Ponto3D;
  n: Ponto3D;
  ondas: { k: number; amplitude: number; fase: number; velocidade: number }[];
  altura: number;
  faseAltura: number;
};

function normalizar(p: Ponto3D): Ponto3D {
  const tamanho = Math.hypot(p.x, p.y, p.z) || 1;
  return { x: p.x / tamanho, y: p.y / tamanho, z: p.z / tamanho };
}

function vetorial(a: Ponto3D, b: Ponto3D): Ponto3D {
  return { x: a.y * b.z - a.z * b.y, y: a.z * b.x - a.x * b.z, z: a.x * b.y - a.y * b.x };
}

/**
 * `quantidade` fios quase de frente para quem olha, cada um um pouco
 * inclinado para um lado: juntos formam um anel de laços com o meio vazio.
 * Sem sorteio: tudo sai do ângulo dourado, e o orbe é sempre o mesmo.
 */
export function criarFios(quantidade: number): Fio[] {
  const anguloDourado = Math.PI * (3 - Math.sqrt(5));
  return Array.from({ length: quantidade }, (_, i) => {
    const inclinacao = 0.22 + ((i * 0.618) % 1) * 0.42; // de ~13° a ~37°
    const direcao = anguloDourado * i;
    const n = {
      x: Math.sin(inclinacao) * Math.cos(direcao),
      y: Math.sin(inclinacao) * Math.sin(direcao),
      z: Math.cos(inclinacao),
    };
    // Qualquer vetor que não seja paralelo à normal serve de referência.
    const referencia = Math.abs(n.y) < 0.9 ? { x: 0, y: 1, z: 0 } : { x: 1, y: 0, z: 0 };
    const u = normalizar(vetorial(n, referencia));
    const v = vetorial(n, u);
    const semente = i * anguloDourado;
    return {
      u,
      v,
      n,
      ondas: [2, 3, 5].map((k, j) => ({
        k,
        amplitude: 0.06 / (j + 1),
        fase: (semente * (j + 1)) % (Math.PI * 2),
        velocidade: (0.3 + ((semente * 7 + j) % 1) * 0.5) * (j % 2 ? -1 : 1),
      })),
      altura: 0.12 + ((i * 0.381) % 1) * 0.12,
      faseAltura: (semente * 3) % (Math.PI * 2),
    };
  });
}

/**
 * O ponto do fio no ângulo `angulo` (0 a 2π), em segundos `tempo`. Com
 * `energia` (a voz, de 0 a 1), o fio se agita mais e o orbe se abre.
 */
export function pontoDoFio(fio: Fio, angulo: number, tempo: number, energia: number): Ponto3D {
  const agito = 0.6 + energia * 1.6;
  let raio = 1;
  for (const onda of fio.ondas) {
    raio += onda.amplitude * agito * Math.sin(onda.k * angulo + onda.fase + tempo * onda.velocidade);
  }
  const fora = fio.altura * agito * Math.sin(2 * angulo + fio.faseAltura + tempo * 0.7);
  const c = Math.cos(angulo) * raio;
  const s = Math.sin(angulo) * raio;
  return {
    x: fio.u.x * c + fio.v.x * s + fio.n.x * fora,
    y: fio.u.y * c + fio.v.y * s + fio.n.y * fora,
    z: fio.u.z * c + fio.v.z * s + fio.n.z * fora,
  };
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
