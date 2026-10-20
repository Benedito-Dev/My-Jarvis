import { type RefObject, useEffect, useRef, useState } from "react";
import { ouvirVozDoJarvis } from "../api";
import { nivelNoInstante } from "../voz";

// Se o canal cair (backend reiniciando), tenta de novo depois disto.
const ESPERA_PARA_RECONECTAR_MS = 2000;

export type VozDoJarvis = {
  /** Volume da voz do Jarvis agora, de 0 a 1 (do envelope real da fala). */
  nivel: RefObject<number>;
  /** Está falando agora (pelo envelope, não por estimativa). */
  falando: boolean;
  /** O backend mede o envelope (voz Piper). Sem isso, o app volta à estimativa. */
  temEnvelope: boolean;
};

/**
 * Ouve o canal /voz/eventos do backend: a cada fala que começa, chega o volume
 * dela a cada 40 ms. Assim o núcleo pulsa com a voz de verdade, inclusive em
 * lembretes, que não passam pela conversa.
 */
export function useVozDoJarvis(): VozDoJarvis {
  const nivel = useRef(0);
  const [falando, setFalando] = useState(false);
  const [temEnvelope, setTemEnvelope] = useState(false);

  useEffect(() => {
    let ativo = true;
    const cancelar = new AbortController();
    let fala: { inicio: number; envelope: number[]; passo: number } | null = null;
    let fimDaFala = 0;
    let quadro = 0;

    const acompanhar = () => {
      nivel.current = fala
        ? nivelNoInstante(fala.envelope, fala.passo, performance.now() - fala.inicio)
        : 0;
      quadro = requestAnimationFrame(acompanhar);
    };
    quadro = requestAnimationFrame(acompanhar);

    async function ouvir() {
      while (ativo) {
        try {
          await ouvirVozDoJarvis((evento) => {
            if (evento.tipo !== "fala" || !evento.envelope?.length) return;
            fala = { inicio: performance.now(), envelope: evento.envelope, passo: evento.passo_ms };
            setTemEnvelope(true);
            setFalando(true);
            window.clearTimeout(fimDaFala);
            fimDaFala = window.setTimeout(
              () => setFalando(false),
              evento.envelope.length * evento.passo_ms,
            );
          }, cancelar.signal);
        } catch {
          // backend fora do ar ou reiniciando: tenta de novo daqui a pouco
        }
        if (ativo) await new Promise((r) => setTimeout(r, ESPERA_PARA_RECONECTAR_MS));
      }
    }
    ouvir();

    return () => {
      ativo = false;
      cancelar.abort();
      cancelAnimationFrame(quadro);
      window.clearTimeout(fimDaFala);
    };
  }, []);

  return { nivel, falando, temEnvelope };
}
