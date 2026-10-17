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

/** Texto e cor para cada momento da gravação. */
export function aparencia(gravacao: EstadoGravacao): { mensagem: string; tom: Tom } {
  switch (gravacao.estado) {
    case "parado":
      return { mensagem: "Segure ESPAÇO para falar", tom: "aviso" };
    case "gravando":
      return { mensagem: "Gravando... solte para guardar", tom: "ok" };
    case "enviando":
      return { mensagem: "Guardando...", tom: "aviso" };
    case "guardada":
      return { mensagem: `Guardado em ${gravacao.arquivo}`, tom: "ok" };
    case "erro":
      return { mensagem: gravacao.mensagem, tom: "erro" };
  }
}
