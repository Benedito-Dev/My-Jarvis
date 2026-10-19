import { useEffect, useState } from "react";
import { trechoDigitado } from "../digitando";

const MS_POR_LETRA = 28;

/** Revela o texto como se o Jarvis estivesse digitando. Recomeça quando o texto muda. */
export function useDigitando(texto: string): string {
  const [visivel, setVisivel] = useState("");

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setVisivel(texto);
      return;
    }
    const inicio = performance.now();
    let quadro = 0;
    const passo = (agora: number) => {
      const trecho = trechoDigitado(texto, agora - inicio, MS_POR_LETRA);
      setVisivel(trecho);
      if (trecho.length < texto.length) quadro = requestAnimationFrame(passo);
    };
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [texto]);

  return visivel;
}
