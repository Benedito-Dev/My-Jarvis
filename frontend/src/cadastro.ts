import type { EstadoCadastro } from "./api";
import type { Tom } from "./desbloqueio";

// Mesma regra do backend (`banco_rostos.validar_nome`): só o que vira nome de
// arquivo seguro. Validar aqui também evita gastar 5 fotos para o backend
// recusar no fim.
const NOME_VALIDO = /^[\w-]+$/;

export function nomeInvalido(nome: string): string | null {
  const limpo = nome.trim();
  if (!limpo) return "Digite um nome.";
  if (!NOME_VALIDO.test(limpo)) return "Use só letras, números, - ou _ (sem espaços nem acentos).";
  return null;
}

/** Texto e cor para cada resposta do backend durante o cadastro. */
export function aparencia(
  estado: EstadoCadastro,
  capturadas: number,
  necessarias: number,
): { mensagem: string; tom: Tom } {
  const tabela: Record<EstadoCadastro, { mensagem: string; tom: Tom }> = {
    sem_rosto: { mensagem: "Nenhum rosto. Aproxime-se da câmera", tom: "aviso" },
    varios_rostos: { mensagem: "Apenas uma pessoa por vez", tom: "aviso" },
    longe: { mensagem: "Por favor, aproxime seu rosto", tom: "aviso" },
    capturada: {
      mensagem: `Capturada ${capturadas} de ${necessarias}. Vire o rosto um pouco`,
      tom: "ok",
    },
    concluido: { mensagem: "Rosto cadastrado!", tom: "ok" },
  };
  return tabela[estado];
}
