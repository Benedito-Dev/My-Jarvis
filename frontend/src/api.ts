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

export type Sessao = {
  usuario: string | null; // null = bloqueado
};

export type EstadoDesbloqueio =
  | "sem_rosto"
  | "varios_rostos"
  | "longe"
  | "desconhecido"
  | "reconhecendo"
  | "desbloqueado";

export type Retangulo = {
  topo: number;
  direita: number;
  base: number;
  esquerda: number;
};

export type Avaliacao = {
  estado: EstadoDesbloqueio;
  progresso: number;
  usuario: string | null;
  rostos: Retangulo[];
};

async function requisitar<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const resposta = await fetch(`${URL_BACKEND}${caminho}`, {
    ...opcoes,
    signal: AbortSignal.timeout(TEMPO_LIMITE_MS),
  });
  if (!resposta.ok) {
    // O FastAPI devolve o motivo do erro em { detail: "..." }
    const corpo = await resposta.json().catch(() => null);
    throw new Error(corpo?.detail ?? `Backend respondeu ${resposta.status} em ${caminho}`);
  }
  return resposta.json();
}

export const buscarStatus = () => requisitar<Status>("/status");
export const buscarRostos = () => requisitar<Rostos>("/rostos");
export const buscarSessao = () => requisitar<Sessao>("/sessao");

// Tranca o Jarvis de novo. Quem decide o estado é o backend, nunca o app:
// enquanto a sessão lá estiver aberta, qualquer rosto entra sem ser avaliado.
export const bloquearSessao = () =>
  requisitar<Sessao>("/sessao/bloquear", { method: "POST" });

export const enviarQuadro = (jpeg: Blob) =>
  requisitar<Avaliacao>("/desbloqueio/quadro", {
    method: "POST",
    headers: { "Content-Type": "image/jpeg" },
    body: jpeg,
  });
