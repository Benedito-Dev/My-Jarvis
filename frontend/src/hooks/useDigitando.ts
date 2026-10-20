import { useEffect, useRef, useState } from "react";
import { trechoDigitado } from "../digitando";

export const MS_POR_LETRA = 28;

/**
 * Revela o texto como se o Jarvis estivesse digitando. Se o texto novo só
 * acrescenta ao anterior (a resposta crescendo frase a frase), continua de onde
 * parou; se é outro texto, recomeça. `atraso` espera antes da primeira letra.
 */
export function useDigitando(texto: string, atraso = 0): string {
  const [visivel, setVisivel] = useState("");
  const mostrado = useRef("");

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setVisivel(texto);
      mostrado.current = texto;
      return;
    }
    const continua = mostrado.current !== "" && texto.startsWith(mostrado.current);
    const jaMostradas = continua ? mostrado.current.length : 0;
    const espera = continua ? 0 : atraso;
    const inicio = performance.now();
    let quadro = 0;
    const passo = (agora: number) => {
      const passado = agora - inicio - espera + jaMostradas * MS_POR_LETRA;
      const trecho = trechoDigitado(texto, passado, MS_POR_LETRA);
      setVisivel(trecho);
      mostrado.current = trecho;
      if (trecho.length < texto.length) quadro = requestAnimationFrame(passo);
    };
    quadro = requestAnimationFrame(passo);
    return () => cancelAnimationFrame(quadro);
  }, [texto, atraso]);

  return visivel;
}
