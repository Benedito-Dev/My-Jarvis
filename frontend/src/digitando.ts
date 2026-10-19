/** Quanto de `texto` já apareceu depois de `passado` ms, digitando uma letra a cada `msPorLetra`. */
export function trechoDigitado(texto: string, passado: number, msPorLetra: number): string {
  const letras = Math.max(0, Math.floor(passado / msPorLetra));
  return texto.slice(0, letras);
}
