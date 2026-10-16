// Ponte com o backend Python (jarvis servidor), que roda só nesta máquina.
export const URL_BACKEND = "http://127.0.0.1:8765";

const TEMPO_LIMITE_MS = 2000;

export type Habilidade = {
  id: string;
  nome: string;
  descricao: string;
  situacao: "pronta" | "em_breve";
};

export type Status = {
  nome: string;
  versao: string;
  habilidades: Habilidade[];
};

export type Rostos = {
  cadastrados: string[];
};

async function buscar<T>(caminho: string): Promise<T> {
  const resposta = await fetch(`${URL_BACKEND}${caminho}`, {
    signal: AbortSignal.timeout(TEMPO_LIMITE_MS),
  });
  if (!resposta.ok) {
    throw new Error(`Backend respondeu ${resposta.status} em ${caminho}`);
  }
  return resposta.json();
}

export const buscarStatus = () => buscar<Status>("/status");
export const buscarRostos = () => buscar<Rostos>("/rostos");
