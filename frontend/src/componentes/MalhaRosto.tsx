import { type RefObject, useEffect, useRef } from "react";
import { FaceLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";
import type { Tom } from "../desbloqueio";
import { type Caixa, type Ponto, caixaDosPontos, noVisor, suavizar } from "../malha";

// A malha do rosto (decisão 0015). O MediaPipe roda aqui no app, a cada quadro
// da câmera, e o desenho acompanha o rosto sem esperar o backend. Quem decide
// QUEM é continua sendo o backend: isto aqui é só o que a pessoa vê.

const PASTA_VISAO = "/visao";
// Quanto cada ponto anda, por quadro, até a posição nova (tira o tremor).
const PESO_SUAVIZACAO = 0.55;
// Uma ida e volta da faixa de varredura pelo rosto.
const VARREDURA_MS = 2200;
// Quanto dura o "pulso" quando o rosto é confirmado.
const PULSO_MS = 900;

// Pedaços da malha que viram traço forte: contorno, olhos, sobrancelhas e boca.
const CONTORNOS = [
  FaceLandmarker.FACE_LANDMARKS_FACE_OVAL,
  FaceLandmarker.FACE_LANDMARKS_LEFT_EYE,
  FaceLandmarker.FACE_LANDMARKS_RIGHT_EYE,
  FaceLandmarker.FACE_LANDMARKS_LEFT_EYEBROW,
  FaceLandmarker.FACE_LANDMARKS_RIGHT_EYEBROW,
  FaceLandmarker.FACE_LANDMARKS_LIPS,
].flat();
const TRIANGULOS = FaceLandmarker.FACE_LANDMARKS_TESSELATION;
// O centro de cada íris (os pontos 468 em diante só existem com o modelo de íris).
const IRIS = [468, 473];

// Um único detector para o app inteiro: carregar leva ~1 s, não vale repetir.
let detectorPromessa: Promise<FaceLandmarker> | null = null;

function carregarDetector(): Promise<FaceLandmarker> {
  detectorPromessa ??= (async () => {
    const arquivos = await FilesetResolver.forVisionTasks(`${PASTA_VISAO}/wasm`);
    const opcoes = (delegate: "GPU" | "CPU") => ({
      baseOptions: { modelAssetPath: `${PASTA_VISAO}/face_landmarker.task`, delegate },
      runningMode: "VIDEO" as const,
      numFaces: 2,
    });
    // GPU (WebGL) quando o WebView deixa; senão CPU, que ainda dá conta.
    try {
      return await FaceLandmarker.createFromOptions(arquivos, opcoes("GPU"));
    } catch {
      return await FaceLandmarker.createFromOptions(arquivos, opcoes("CPU"));
    }
  })();
  return detectorPromessa;
}

type Props = {
  videoRef: RefObject<HTMLVideoElement | null>;
  ligada: boolean;
  tom: Tom;
  /** 0 a 1: quanto do reconhecimento o backend já confirmou. */
  progresso: number;
  confirmado: boolean;
};

export function MalhaRosto({ videoRef, ligada, tom, progresso, confirmado }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // O laço de desenho lê estes valores a cada quadro. Ficam em ref para que
  // mudar o progresso não reinicie o laço (nem o detector).
  const vivo = useRef({ tom, progresso, confirmado, confirmadoEm: 0 });
  useEffect(() => {
    const atual = vivo.current;
    if (confirmado && !atual.confirmado) atual.confirmadoEm = performance.now();
    Object.assign(atual, { tom, progresso, confirmado });
  }, [tom, progresso, confirmado]);

  useEffect(() => {
    if (!ligada) return;
    const canvas = canvasRef.current!;
    const contexto = canvas.getContext("2d")!;
    let ativo = true;
    let quadro = 0;
    let detector: FaceLandmarker | null = null;
    let ultimoTempoVideo = -1;
    let rostos: Ponto[][] = [];

    carregarDetector()
      .then((carregado) => {
        detector = carregado;
      })
      .catch((erro) => console.warn("Malha do rosto indisponível:", erro));

    // O canvas acompanha o tamanho do visor, em pixels reais da tela.
    const ajustarTamanho = () => {
      const escala = window.devicePixelRatio || 1;
      canvas.width = Math.round(canvas.clientWidth * escala);
      canvas.height = Math.round(canvas.clientHeight * escala);
    };
    const observador = new ResizeObserver(ajustarTamanho);
    observador.observe(canvas);
    ajustarTamanho();

    function passo(agora: number) {
      if (!ativo) return;
      const video = videoRef.current;

      // Só roda o detector quando a câmera entregou um quadro novo.
      if (detector && video && video.readyState >= 2 && video.currentTime !== ultimoTempoVideo) {
        ultimoTempoVideo = video.currentTime;
        const resultado = detector.detectForVideo(video, agora);
        const tamanhoVideo = { largura: video.videoWidth, altura: video.videoHeight };
        const visor = { largura: canvas.width, altura: canvas.height };
        rostos = resultado.faceLandmarks.map((pontos, i) =>
          suavizar(
            rostos[i] ?? null,
            pontos.map((p) => noVisor(p, tamanhoVideo, visor)),
            PESO_SUAVIZACAO,
          ),
        );
      }

      desenhar(contexto, canvas, rostos, vivo.current, agora);
      quadro = requestAnimationFrame(passo);
    }
    quadro = requestAnimationFrame(passo);

    return () => {
      ativo = false;
      cancelAnimationFrame(quadro);
      observador.disconnect();
    };
  }, [videoRef, ligada]);

  return <canvas ref={canvasRef} className="visor__malha" aria-hidden="true" />;
}

// --- Desenho -----------------------------------------------------------------

type Estado = { tom: Tom; progresso: number; confirmado: boolean; confirmadoEm: number };

const CORES: Record<Tom, string> = {
  aviso: "57, 197, 255",
  ok: "61, 220, 132",
  erro: "255, 90, 95",
};

function desenhar(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  rostos: Ponto[][],
  estado: Estado,
  agora: number,
) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const escala = canvas.width / 400; // traços proporcionais ao tamanho do visor
  const cor = CORES[estado.confirmado ? "ok" : estado.tom];

  if (rostos.length === 0) {
    desenharMira(ctx, canvas, escala, cor, agora);
    return;
  }
  for (const pontos of rostos) {
    desenharRosto(ctx, pontos, escala, cor, estado, agora);
  }
}

/** Sem rosto: uma mira girando no centro, chamando a pessoa. */
function desenharMira(
  ctx: CanvasRenderingContext2D,
  canvas: HTMLCanvasElement,
  escala: number,
  cor: string,
  agora: number,
) {
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const raio = canvas.width * 0.3;
  const giro = (agora / 2400) * Math.PI * 2;

  ctx.lineWidth = 1.5 * escala;
  ctx.strokeStyle = `rgba(${cor}, 0.55)`;
  for (let i = 0; i < 4; i++) {
    const inicio = giro + (i * Math.PI) / 2;
    ctx.beginPath();
    ctx.arc(cx, cy, raio, inicio, inicio + Math.PI / 5);
    ctx.stroke();
  }
  const respiro = 0.5 + 0.5 * Math.sin(agora / 400);
  ctx.strokeStyle = `rgba(${cor}, ${0.15 + 0.25 * respiro})`;
  ctx.beginPath();
  ctx.ellipse(cx, cy, raio * 0.62, raio * 0.8, 0, 0, Math.PI * 2);
  ctx.stroke();
}

function desenharRosto(
  ctx: CanvasRenderingContext2D,
  pontos: Ponto[],
  escala: number,
  cor: string,
  estado: Estado,
  agora: number,
) {
  const caixa = caixaDosPontos(pontos);
  const altura = caixa.base - caixa.topo;

  // 1. A malha inteira, bem fraca: dá volume 3D ao rosto.
  ctx.lineWidth = 0.6 * escala;
  ctx.strokeStyle = `rgba(${cor}, ${estado.confirmado ? 0.32 : 0.16})`;
  tracar(ctx, pontos, TRIANGULOS);

  // 2. A faixa de varredura: desce e sobe, e acende os pontos por onde passa.
  if (!estado.confirmado) {
    const fase = (agora % VARREDURA_MS) / VARREDURA_MS;
    const y = caixa.topo + altura * (fase < 0.5 ? fase * 2 : 2 - fase * 2);
    const meiaFaixa = altura * 0.09;
    for (const { x, y: py } of pontos) {
      const perto = 1 - Math.abs(py - y) / meiaFaixa;
      if (perto <= 0) continue;
      ctx.fillStyle = `rgba(${cor}, ${perto * 0.95})`;
      ctx.fillRect(x - escala, py - escala, 2 * escala, 2 * escala);
    }
    const brilho = ctx.createLinearGradient(caixa.esquerda, 0, caixa.direita, 0);
    brilho.addColorStop(0, `rgba(${cor}, 0)`);
    brilho.addColorStop(0.5, `rgba(${cor}, 0.8)`);
    brilho.addColorStop(1, `rgba(${cor}, 0)`);
    ctx.strokeStyle = brilho;
    ctx.lineWidth = 1.2 * escala;
    ctx.beginPath();
    ctx.moveTo(caixa.esquerda, y);
    ctx.lineTo(caixa.direita, y);
    ctx.stroke();
  }

  // 3. Contornos fortes, com um halo largo por baixo no lugar de um blur caro.
  ctx.strokeStyle = `rgba(${cor}, 0.18)`;
  ctx.lineWidth = 4 * escala;
  tracar(ctx, pontos, CONTORNOS);
  ctx.strokeStyle = `rgba(${cor}, 0.85)`;
  ctx.lineWidth = 1.1 * escala;
  tracar(ctx, pontos, CONTORNOS);

  // 4. Pontos "travados": acendem conforme o backend vai confirmando quem é.
  const travados = Math.round(estado.progresso * pontos.length);
  ctx.fillStyle = `rgba(${CORES.ok}, 0.9)`;
  for (let i = 0; i < travados; i++) {
    const { x, y } = pontos[(i * 97) % pontos.length];
    ctx.fillRect(x - 0.9 * escala, y - 0.9 * escala, 1.8 * escala, 1.8 * escala);
  }

  // 5. Íris: um anel em cada olho.
  ctx.strokeStyle = `rgba(${cor}, 0.9)`;
  ctx.lineWidth = 1 * escala;
  for (const indice of IRIS) {
    const centro = pontos[indice];
    if (!centro) continue;
    ctx.beginPath();
    ctx.arc(centro.x, centro.y, altura * 0.035, 0, Math.PI * 2);
    ctx.stroke();
  }

  desenharCantoneiras(ctx, caixa, escala, cor);

  // 6. Confirmado: um pulso sai do rosto e se espalha.
  if (estado.confirmado) {
    const passado = (agora - estado.confirmadoEm) / PULSO_MS;
    if (passado < 1) {
      const cx = (caixa.esquerda + caixa.direita) / 2;
      const cy = (caixa.topo + caixa.base) / 2;
      ctx.strokeStyle = `rgba(${CORES.ok}, ${1 - passado})`;
      ctx.lineWidth = 3 * escala * (1 - passado) + 0.5;
      ctx.beginPath();
      ctx.ellipse(cx, cy, altura * (0.4 + passado * 0.6), altura * (0.55 + passado * 0.6), 0, 0, Math.PI * 2);
      ctx.stroke();
    }
  }
}

/** As quatro cantoneiras de mira em volta do rosto. */
function desenharCantoneiras(ctx: CanvasRenderingContext2D, caixa: Caixa, escala: number, cor: string) {
  const folga = (caixa.direita - caixa.esquerda) * 0.12;
  const e = caixa.esquerda - folga;
  const d = caixa.direita + folga;
  const t = caixa.topo - folga;
  const b = caixa.base + folga;
  const braco = (d - e) * 0.14;

  ctx.strokeStyle = `rgba(${cor}, 0.95)`;
  ctx.lineWidth = 1.6 * escala;
  ctx.beginPath();
  for (const [x, y, dx, dy] of [
    [e, t, 1, 1],
    [d, t, -1, 1],
    [e, b, 1, -1],
    [d, b, -1, -1],
  ]) {
    ctx.moveTo(x + dx * braco, y);
    ctx.lineTo(x, y);
    ctx.lineTo(x, y + dy * braco);
  }
  ctx.stroke();
}

/** Traça várias ligações de uma vez, num caminho só (bem mais rápido). */
function tracar(ctx: CanvasRenderingContext2D, pontos: Ponto[], ligacoes: { start: number; end: number }[]) {
  ctx.beginPath();
  for (const { start, end } of ligacoes) {
    const a = pontos[start];
    const b = pontos[end];
    if (!a || !b) continue;
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
  }
  ctx.stroke();
}
