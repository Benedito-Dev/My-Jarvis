import { type RefObject, useEffect, useRef } from "react";
import type { TomNucleo } from "../gravacao";
import { type Fio, criarFios, girar, pontoDoFio } from "../nucleo";

// O núcleo do painel: um orbe de fios de luz entrelaçados, girando devagar.
// Parado, ele respira; com voz (a sua ou a do Jarvis), os fios se agitam e o
// orbe se abre no ritmo do volume real. É o "rosto" do Jarvis.

const FIOS = criarFios(14);
const PONTOS_POR_FIO = 128;
// O fio é desenhado em trechos: cada trecho tem o brilho da sua profundidade
// (o que está atrás fica apagado), e é isso que dá volume ao novelo.
const PONTOS_POR_TRECHO = 8;

const CORES: Record<TomNucleo, string> = {
  aviso: "57, 197, 255",
  ok: "61, 220, 132",
  erro: "255, 90, 95",
  pensando: "169, 112, 255",
};

/**
 * Como a esfera se comporta: em repouso, ouvindo, pensando ou falando.
 * "voz" é falando com o volume real da fala (canal /voz/eventos); "falando" é a
 * estimativa, para quando o backend não mede a voz (sem Piper).
 */
export type ModoNucleo = "calmo" | "ouvindo" | "pensando" | "falando" | "voz";

// "Energia" mínima de cada modo, antes de qualquer som. Ouvindo, a voz soma por
// cima; pensando, a esfera pulsa sozinha entre o repouso e a fala.
function energiaDoModo(modo: ModoNucleo, agora: number): number {
  if (modo === "ouvindo") return 0.18;
  if (modo === "voz") return 0.08; // o resto vem do volume real da fala
  if (modo === "pensando") return 0.42 + Math.sin(agora / 260) * 0.14;
  if (modo === "falando") {
    // Pulsos curtos, como sílabas, dentro de uma "frase" que sobe e desce.
    const silaba = Math.abs(Math.sin(agora / 85));
    const frase = 0.6 + 0.4 * Math.sin(agora / 380);
    return 0.2 + silaba * frase * 0.55;
  }
  return 0;
}

type Props = {
  /** Volumes que agitam a esfera (o microfone e a voz do Jarvis): vale o maior. */
  niveis: RefObject<number>[];
  tom: TomNucleo;
  modo: ModoNucleo;
};

export function Nucleo({ niveis, tom, modo }: Props) {
  const niveisRef = useRef(niveis);
  niveisRef.current = niveis;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tomRef = useRef(tom);
  tomRef.current = tom;
  const modoRef = useRef(modo);
  modoRef.current = modo;

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const calmo = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let quadro = 0;
    let energia = 0; // o volume suavizado: sobe rápido, desce devagar
    let giro = 0; // ângulo da esfera: acumulado, porque a velocidade muda com a voz
    let anterior = 0;

    const ajustarTamanho = () => {
      const escala = window.devicePixelRatio || 1;
      canvas.width = Math.round(canvas.clientWidth * escala);
      canvas.height = Math.round(canvas.clientHeight * escala);
    };
    const observador = new ResizeObserver(ajustarTamanho);
    observador.observe(canvas);
    ajustarTamanho();

    function passo(agora: number) {
      const intervalo = anterior ? Math.min(agora - anterior, 50) : 16;
      anterior = agora;
      const volume = Math.max(0, ...niveisRef.current.map((n) => n.current ?? 0));
      const alvo = Math.max(volume, energiaDoModo(modoRef.current, agora));
      energia += (alvo - energia) * (alvo > energia ? 0.45 : 0.1);
      // Parada, uma volta a cada ~26 s; falando alto, umas 6 vezes mais rápido.
      if (!calmo) giro += intervalo * (0.00024 + energia * 0.0014);
      desenhar(ctx, canvas, calmo ? 0 : agora, giro, energia, CORES[tomRef.current]);
      quadro = requestAnimationFrame(passo);
    }
    quadro = requestAnimationFrame(passo);

    return () => {
      cancelAnimationFrame(quadro);
      observador.disconnect();
    };
  }, []);

  return <canvas ref={canvasRef} className="nucleo" aria-hidden="true" />;
}

function desenhar(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  agora: number,
  giro: number,
  energia: number,
  cor: string,
) {
  const { width: largura, height: altura } = canvas;
  const cx = largura / 2;
  const cy = altura / 2;
  const R = Math.min(largura, altura) / 2;
  const traco = R / 220; // espessuras proporcionais ao tamanho do núcleo
  const tempo = agora / 1000;
  const claro = clarear(cor, 0.55);
  ctx.clearRect(0, 0, largura, altura);

  // 1. Brilho de fundo: uma névoa que cresce com a voz.
  const brilho = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * (0.7 + energia * 0.2));
  brilho.addColorStop(0, `rgba(${cor}, ${0.1 + energia * 0.18})`);
  brilho.addColorStop(0.6, `rgba(${cor}, ${0.04 + energia * 0.06})`);
  brilho.addColorStop(1, `rgba(${cor}, 0)`);
  ctx.fillStyle = brilho;
  ctx.fillRect(0, 0, largura, altura);

  // "lighter" soma as luzes: onde os fios se cruzam, o brilho fica mais forte.
  ctx.globalCompositeOperation = "lighter";
  // Pontas retas: com pontas redondas, a luz somava duas vezes em cada emenda
  // de trecho e o fio parecia pontilhado.
  ctx.lineCap = "butt";
  ctx.lineJoin = "round";

  // 2. Onda de choque: anéis finos que saem do orbe com a força da voz.
  if (energia > 0.05) {
    for (const atraso of [0, 450]) {
      const fase = ((agora + atraso) % 900) / 900;
      ctx.strokeStyle = `rgba(${cor}, ${(1 - fase) * Math.min(0.6, energia)})`;
      ctx.lineWidth = 1.2 * traco;
      ctx.beginPath();
      ctx.arc(cx, cy, R * (0.66 + fase * 0.3), 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  // 3. Os fios: cada um em duas passadas, um halo largo e fraco e o fio fino
  //    e claro por cima. Juntos, parecem luz de verdade (sem filtro de blur).
  const respiro = 1 + Math.sin(agora / 1100) * 0.02;
  const raio = R * 0.58 * respiro * (1 + energia * 0.22);
  // O anel balança de leve (para se ver a profundidade) e gira no plano da tela.
  const emY = Math.sin(agora / 5000) * 0.25;
  const emX = Math.sin(agora / 6500) * 0.2;
  for (let f = 0; f < FIOS.length; f++) {
    const pontos = projetarFio(FIOS[f], tempo, energia, emY, emX, giro);
    for (let i = 0; i < PONTOS_POR_FIO; i += PONTOS_POR_TRECHO) {
      const meio = pontos[(i + PONTOS_POR_TRECHO / 2) % PONTOS_POR_FIO];
      const frente = (meio.z + 1) / 2; // 0 = fundo, 1 = frente
      const forca = 0.15 + frente * 0.85;
      ctx.beginPath();
      for (let j = 0; j <= PONTOS_POR_TRECHO; j++) {
        const p = pontos[(i + j) % PONTOS_POR_FIO];
        const x = cx + p.x * raio;
        const y = cy + p.y * raio;
        if (j === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.strokeStyle = `rgba(${cor}, ${forca * (0.07 + energia * 0.06)})`;
      ctx.lineWidth = (7 + energia * 5) * traco;
      ctx.stroke();
      ctx.strokeStyle = `rgba(${claro}, ${forca * (0.55 + energia * 0.35)})`;
      ctx.lineWidth = (1 + energia * 0.6) * traco;
      ctx.stroke();
    }

    // 4. Faíscas: um ponto de luz que corre por alguns fios, como um sinal.
    if (f % 3 === 0) {
      const posicao = Math.floor((((agora / 4200) * (1 + f * 0.13) + f * 0.37) % 1) * PONTOS_POR_FIO);
      const p = pontos[posicao];
      const frente = (p.z + 1) / 2;
      const x = cx + p.x * raio;
      const y = cy + p.y * raio;
      const tamanho = (10 + energia * 8) * traco;
      const faisca = ctx.createRadialGradient(x, y, 0, x, y, tamanho);
      faisca.addColorStop(0, `rgba(${claro}, ${0.25 + frente * 0.7})`);
      faisca.addColorStop(1, `rgba(${cor}, 0)`);
      ctx.fillStyle = faisca;
      ctx.fillRect(x - tamanho, y - tamanho, tamanho * 2, tamanho * 2);
    }
  }

  ctx.globalCompositeOperation = "source-over";
}

/**
 * Os pontos de um fio já virados para a câmera (x, y na tela; z = profundidade),
 * e girados `noPlano` radianos em volta do centro da tela.
 */
function projetarFio(
  fio: Fio,
  tempo: number,
  energia: number,
  emY: number,
  emX: number,
  noPlano: number,
) {
  const cos = Math.cos(noPlano);
  const sen = Math.sin(noPlano);
  return Array.from({ length: PONTOS_POR_FIO }, (_, i) => {
    const p = girar(pontoDoFio(fio, (i / PONTOS_POR_FIO) * Math.PI * 2, tempo, energia), emY, emX);
    return { x: p.x * cos - p.y * sen, y: p.x * sen + p.y * cos, z: p.z };
  });
}

/** Mistura a cor "r, g, b" com branco: o miolo do fio é mais claro que o halo. */
function clarear(cor: string, quanto: number): string {
  return cor
    .split(",")
    .map((canal) => Math.round(Number(canal) + (255 - Number(canal)) * quanto))
    .join(", ");
}
