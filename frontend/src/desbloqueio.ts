import type { EstadoDesbloqueio } from "./api";

export type Tom = "aviso" | "erro" | "ok";

// Texto e cor da tela de bloqueio para cada resposta do backend.
export function aparencia(estado: EstadoDesbloqueio, usuario: string | null) {
  const tabela: Record<EstadoDesbloqueio, { mensagem: string; tom: Tom }> = {
    sem_rosto: { mensagem: "Por favor, aproxime seu rosto", tom: "aviso" },
    longe: { mensagem: "Por favor, aproxime seu rosto", tom: "aviso" },
    varios_rostos: { mensagem: "Apenas uma pessoa por vez", tom: "aviso" },
    desconhecido: { mensagem: "Acesso negado", tom: "erro" },
    reconhecendo: { mensagem: "Reconhecendo...", tom: "ok" },
    desbloqueado: { mensagem: `Bem-vindo, ${usuario ?? ""}`.trim(), tom: "ok" },
  };
  return tabela[estado];
}
