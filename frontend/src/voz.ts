// Lógica pura do canal da voz do Jarvis (núcleo pulsando com a fala real).

/** Evento do canal /voz/eventos: uma fala começou (ou só um "pulso" de vida). */
export type EventoVoz =
  { tipo: "fala"; frase: string; envelope: number[] | null; passo_ms: number } | { tipo: "pulso" };

/** O volume da fala `decorridoMs` depois de ela começar (0 antes e depois). */
export function nivelNoInstante(envelope: number[], passoMs: number, decorridoMs: number): number {
  if (decorridoMs < 0) return 0;
  return envelope[Math.floor(decorridoMs / passoMs)] ?? 0;
}
