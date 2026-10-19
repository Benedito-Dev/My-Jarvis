import { type RefObject, useEffect, useRef } from "react";
import type { Tom } from "../desbloqueio";
import { girar, pontosNaEsfera } from "../nucleo";

// O núcleo do painel: uma esfera de partículas girando, cercada de anéis.
// Parado, ela respira devagar; segurando ESPAÇO, pulsa com o volume real da voz.
// É o "rosto" do Jarvis: a forma é enfeite, mas o pulso é a sua voz de verdade.

const ESFERA = pontosNaEsfera(520);
// Cada partícula oscila no seu próprio ritmo quando há voz (fase fixa por ponto).
const FASES = ESFERA.map((_, i) => (i * 2.399) % (Math.PI * 2));
const RISCOS = 72;

const CORES: Record<Tom, string> = {
  aviso: "57, 197, 255",
  ok: "61, 220, 132",
  erro: "255, 90, 95",
};

type Props = {
  nivel: RefObject<number>;
  tom: Tom;
};

export function Nucleo({ nivel, tom }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const tomRef = useRef(tom);
  tomRef.current = tom;

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const calmo = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let quadro = 0;
    let energia = 0; // o volume suavizado: sobe rápido, desce devagar

    const ajustarTamanho = () => {
      const escala = window.devicePixelRatio || 1;
      canvas.width = Math.round(canvas.clientWidth * escala);
      canvas.height = Math.round(canvas.clientHeight * escala);
    };
    const observador = new ResizeObserver(ajustarTamanho);
    observador.observe(canvas);
    ajustarTamanho();

    function passo(agora: number) {
      const alvo = nivel.current ?? 0;
      energia += (alvo - energia) * (alvo > energia ? 0.35 : 0.08);
      desenhar(ctx, canvas, calmo ? 0 : agora, energia, CORES[tomRef.current]);
      quadro = requestAnimationFrame(passo);
    }
    quadro = requestAnimationFrame(passo);

    return () => {
      cancelAnimationFrame(quadro);
      observador.disconnect();
    };
  }, [nivel]);

  return <canvas ref={canvasRef} className="nucleo" aria-hidden="true" />;
}

function desenhar(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  agora: number,
  energia: number,
  cor: string,
) {
  const { width: largura, height: altura } = canvas;
  const cx = largura / 2;
  const cy = altura / 2;
  const R = Math.min(largura, altura) / 2;
  const traco = R / 220; // espessuras proporcionais ao tamanho do núcleo
  ctx.clearRect(0, 0, largura, altura);

  // 1. Brilho de fundo: cresce com a voz.
  const brilho = ctx.createRadialGradient(cx, cy, 0, cx, cy, R * (0.55 + energia * 0.25));
  brilho.addColorStop(0, `rgba(${cor}, ${0.22 + energia * 0.3})`);
  brilho.addColorStop(1, `rgba(${cor}, 0)`);
  ctx.fillStyle = brilho;
  ctx.fillRect(0, 0, largura, altura);

  // 2. Coroa de risquinhos girando devagar; os maiores a cada 45°.
  const giroCoroa = agora / 9000;
  ctx.strokeStyle = `rgba(${cor}, 0.45)`;
  ctx.lineWidth = 1.2 * traco;
  ctx.beginPath();
  for (let i = 0; i < RISCOS; i++) {
    const angulo = giroCoroa + (i / RISCOS) * Math.PI * 2;
    const longo = i % 9 === 0;
    const r1 = R * 0.94;
    const r2 = R * (longo ? 0.86 : 0.9);
    ctx.moveTo(cx + Math.cos(angulo) * r1, cy + Math.sin(angulo) * r1);
    ctx.lineTo(cx + Math.cos(angulo) * r2, cy + Math.sin(angulo) * r2);
  }
  ctx.stroke();

  // 3. Arcos girando em sentidos opostos.
  arco(ctx, cx, cy, R * 0.8, agora / 2600, 1.4, `rgba(${cor}, 0.6)`, 2 * traco);
  arco(ctx, cx, cy, R * 0.8, agora / 2600 + Math.PI, 0.6, `rgba(${cor}, 0.6)`, 2 * traco);
  arco(ctx, cx, cy, R * 0.74, -agora / 3400, 2.2, `rgba(${cor}, 0.3)`, 1 * traco);

  // 4. Onda de choque: um anel que se expande com a força da voz.
  if (energia > 0.05) {
    const fase = (agora % 900) / 900;
    ctx.strokeStyle = `rgba(${cor}, ${(1 - fase) * energia * 0.8})`;
    ctx.lineWidth = 2 * traco;
    ctx.beginPath();
    ctx.arc(cx, cy, R * (0.5 + fase * 0.3), 0, Math.PI * 2);
    ctx.stroke();
  }

  // 5. A esfera de partículas: gira, respira e se agita com a voz.
  const respiro = 1 + Math.sin(agora / 900) * 0.025;
  const raio = R * 0.46 * respiro * (1 + energia * 0.18);
  const emY = agora / 4200;
  const emX = 0.42 + Math.sin(agora / 6000) * 0.12;
  for (let i = 0; i < ESFERA.length; i++) {
    const p = girar(ESFERA[i], emY, emX);
    const agito = 1 + energia * 0.22 * Math.sin(FASES[i] + agora / 110);
    const profundidade = (p.z + 1) / 2; // 0 = fundo, 1 = frente
    const tamanho = (0.8 + profundidade * 1.6) * traco * (1 + energia * 0.6);
    ctx.fillStyle = `rgba(${cor}, ${0.12 + profundidade * 0.78})`;
    ctx.fillRect(cx + p.x * raio * agito - tamanho / 2, cy + p.y * raio * agito - tamanho / 2, tamanho, tamanho);
  }

  // 6. O "olho" no centro.
  ctx.fillStyle = `rgba(${cor}, ${0.55 + energia * 0.45})`;
  ctx.beginPath();
  ctx.arc(cx, cy, R * (0.035 + energia * 0.02), 0, Math.PI * 2);
  ctx.fill();
}

function arco(
  ctx: CanvasRenderingContext2D,
  cx: number,
  cy: number,
  raio: number,
  inicio: number,
  comprimento: number,
  estilo: string,
  espessura: number,
) {
  ctx.strokeStyle = estilo;
  ctx.lineWidth = espessura;
  ctx.beginPath();
  ctx.arc(cx, cy, raio, inicio, inicio + comprimento);
  ctx.stroke();
}
