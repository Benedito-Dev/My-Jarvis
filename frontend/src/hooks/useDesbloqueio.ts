import { useEffect, useState, type RefObject } from "react";
import { enviarQuadro, type Avaliacao } from "../api";
import { capturar } from "../quadro";

// Pausas do laço: entre quadros, e depois de um erro (para não martelar o backend).
const PAUSA_ENTRE_QUADROS_MS = 80;
const PAUSA_APOS_ERRO_MS = 1000;

export type Desbloqueio = {
  avaliacao: Avaliacao | null;
  erro: string | null;
  altura: number; // altura do quadro enviado (a largura é LARGURA_QUADRO)
};

const esperar = (ms: number) => new Promise((resolver) => setTimeout(resolver, ms));

/**
 * Enquanto `ligado`, tira fotos do <video>, manda ao backend e guarda a resposta.
 * Para sozinho quando o backend responde que desbloqueou.
 */
export function useDesbloqueio(
  videoRef: RefObject<HTMLVideoElement | null>,
  ligado: boolean,
): Desbloqueio {
  const [desbloqueio, setDesbloqueio] = useState<Desbloqueio>({
    avaliacao: null,
    erro: null,
    altura: 360,
  });

  useEffect(() => {
    if (!ligado) return;
    let ativo = true;
    const canvas = document.createElement("canvas");

    async function laco() {
      while (ativo) {
        const video = videoRef.current;
        if (!video || video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA) {
          await esperar(100);
          continue;
        }

        const jpeg = await capturar(video, canvas);
        try {
          const avaliacao = await enviarQuadro(jpeg);
          if (!ativo) return;
          setDesbloqueio({ avaliacao, erro: null, altura: canvas.height });
          if (avaliacao.estado === "desbloqueado") return;
          await esperar(PAUSA_ENTRE_QUADROS_MS);
        } catch (erro) {
          if (!ativo) return;
          setDesbloqueio((atual) => ({
            ...atual,
            erro: erro instanceof Error ? erro.message : String(erro),
          }));
          await esperar(PAUSA_APOS_ERRO_MS);
        }
      }
    }

    laco();
    return () => {
      ativo = false;
    };
  }, [videoRef, ligado]);

  return desbloqueio;
}
