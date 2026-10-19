import type { Tom } from "./desbloqueio";

export type EstadoGravacao =
  | { estado: "parado" }
  | { estado: "gravando" }
  | { estado: "enviando" }
  | { estado: "guardada"; arquivo: string }
  | { estado: "erro"; mensagem: string };

// Formatos que o MediaRecorder pode entregar, do mais provável ao menos.
// Cada sistema suporta os seus: o WebKitGTK (Linux) costuma dar webm/ogg e o
// WKWebView (macOS) dá mp4. O backend aceita todos estes.
export const FORMATOS = ["audio/webm", "audio/ogg", "audio/mp4"] as const;

/** Primeiro formato que este sistema sabe gravar, ou null se não souber nenhum. */
export function escolherFormato(suportado: (tipo: string) => boolean): string | null {
  return FORMATOS.find((formato) => suportado(formato)) ?? null;
}

/** As cores do núcleo: as da tela de bloqueio, mais o roxo de quando está pensando. */
export type TomNucleo = Tom | "pensando";

/** O que o núcleo do painel diz em cada momento: um título curto e um detalhe. */
export function estadoDoNucleo(gravacao: EstadoGravacao): {
  titulo: string;
  detalhe: string;
  tom: TomNucleo;
} {
  switch (gravacao.estado) {
    case "parado":
      return { titulo: "À sua disposição", detalhe: "Segure ESPAÇO para falar", tom: "aviso" };
    case "gravando":
      return { titulo: "Estou ouvindo", detalhe: "Solte ESPAÇO quando terminar", tom: "ok" };
    case "enviando":
      // Hoje ele só guarda o áudio; com a Fase 3, aqui ele transcreve e pensa na resposta.
      return { titulo: "Pensando", detalhe: "Processando o que você disse...", tom: "pensando" };
    case "guardada":
      // Azul de novo: verde é só enquanto está ouvindo.
      return { titulo: "Ouvi você", detalhe: `Gravação guardada: ${gravacao.arquivo}`, tom: "aviso" };
    case "erro":
      return { titulo: "Não consegui ouvir", detalhe: gravacao.mensagem, tom: "erro" };
  }
}
