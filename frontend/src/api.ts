// Ponte com o backend Python (jarvis servidor), que roda só nesta máquina.
export const URL_BACKEND = "http://127.0.0.1:8765";

const TEMPO_LIMITE_MS = 2000;

export type Habilidade = {
  id: string;
  nome: string;
  descricao: string;
};

export type Status = {
  nome: string;
  versao: string;
  habilidades: Habilidade[];
};

export async function buscarStatus(): Promise<Status> {
  const resposta = await fetch(`${URL_BACKEND}/status`, {
    signal: AbortSignal.timeout(TEMPO_LIMITE_MS),
  });
  if (!resposta.ok) {
    throw new Error(`Backend respondeu ${resposta.status}`);
  }
  return resposta.json();
}
