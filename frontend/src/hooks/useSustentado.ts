import { useEffect, useState } from "react";

/**
 * `ligado` com uma folga para desligar: liga na hora, mas só desliga depois de
 * passar `folgaMs` desligado. Serve para a pausa entre duas frases da fala não
 * parecer o fim da resposta.
 */
export function useSustentado(ligado: boolean, folgaMs: number): boolean {
  const [sustentado, setSustentado] = useState(ligado);

  useEffect(() => {
    if (ligado) {
      setSustentado(true);
      return;
    }
    const temporizador = setTimeout(() => setSustentado(false), folgaMs);
    return () => clearTimeout(temporizador);
  }, [ligado, folgaMs]);

  return ligado || sustentado;
}
