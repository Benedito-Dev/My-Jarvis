import { useEffect, useState } from "react";
import { trechoDigitado } from "../digitando";

export const MS_POR_LETRA = 28;

/**
 * Revela o texto como se o Jarvis estivesse digitando. Recomeça quando o texto
 * muda. `atraso` espera antes da primeira letra (para uma linha vir depois da outra).
 */
export function useDigitando(texto: string, atraso = 0): string {
  const [visivel, setVisivel] = useState("");

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setVisivel(texto);
      return;
    }
    const inicio = performance.now();
    let quadro = 0;
    const passo = (agora: number) => {
      const trecho = trechoDigitado(texto, agora - inicio - atraso, MS_POR_LETRA);
      setVisivel(trecho);
      if (trecho.length < texto.length) quadro = requestAnimationFrame(passo);
    };
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [texto, atraso]);

  return visivel;
}
