import { type RefObject, useEffect, useRef } from "react";

// A onda da voz na faixa de conversa: barras que andam da direita para a
// esquerda com o volume real do microfone. Em silêncio, uma linha quase parada.

const BARRAS = 64;

export function OndaVoz({ nivel, cor }: { nivel: RefObject<number>; cor: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const corRef = useRef(cor);
  corRef.current = cor;

  useEffect(() => {
    const canvas = canvasRef.current!;
    const ctx = canvas.getContext("2d")!;
    const historico = new Array<number>(BARRAS).fill(0);
    let quadro = 0;
    let ultimoEmpurrao = 0;

    const ajustarTamanho = () => {
      const escala = window.devicePixelRatio || 1;
      canvas.width = Math.round(canvas.clientWidth * escala);
      canvas.height = Math.round(canvas.clientHeight * escala);
    };
    const observador = new ResizeObserver(ajustarTamanho);
    observador.observe(canvas);
    ajustarTamanho();

    function passo(agora: number) {
      // Uma barra nova a cada 40 ms: rápido para parecer vivo, lento para dar para ler.
      if (agora - ultimoEmpurrao > 40) {
        historico.shift();
        historico.push(nivel.current ?? 0);
        ultimoEmpurrao = agora;
      }

      const { width: largura, height: altura } = canvas;
      ctx.clearRect(0, 0, largura, altura);
      const passoX = largura / BARRAS;
      const meio = altura / 2;
      for (let i = 0; i < BARRAS; i++) {
        const repouso = 0.04 + 0.03 * Math.sin(agora / 500 + i * 0.4);
        const h = Math.max(repouso, historico[i]) * altura * 0.9;
        // As barras somem nas pontas, para a onda "sair" do nada.
        const borda = Math.sin((i / (BARRAS - 1)) * Math.PI);
        ctx.fillStyle = `rgba(${corRef.current}, ${0.25 + borda * 0.7})`;
        ctx.fillRect(i * passoX + passoX * 0.25, meio - h / 2, passoX * 0.5, h);
      }
      quadro = requestAnimationFrame(passo);
    }
    quadro = requestAnimationFrame(passo);

    return () => {
      cancelAnimationFrame(quadro);
      observador.disconnect();
    };
  }, [nivel]);

  return <canvas ref={canvasRef} className="onda-voz" aria-hidden="true" />;
}
