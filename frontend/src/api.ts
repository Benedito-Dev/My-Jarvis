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

// Os cinco pontos que o YuNet já calcula para alinhar o rosto antes de reconhecer.
export type NomeDoPonto =
  | "olho_direito"
  | "olho_esquerdo"
  | "nariz"
  | "boca_direita"
  | "boca_esquerda";

export type Ponto = {
  nome: NomeDoPonto;
  x: number;
  y: number;
};

export type Retangulo = {
  topo: number;
  direita: number;
  base: number;
  esquerda: number;
  pontos: Ponto[];
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

export const desbloquearPorPin = (identificador: string, pin: string) =>
  requisitar<Sessao>("/sessao/pin", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identificador, pin }),
  });

export const configurarPin = (identificador: string, pin: string) =>
  requisitar<{ configurado: boolean }>("/sessao/pin/configurar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ identificador, pin }),
  });

// Tranca o Jarvis de novo. Quem decide o estado é o backend, nunca o app:
// enquanto a sessão lá estiver aberta, qualquer rosto entra sem ser avaliado.
export const bloquearSessao = () =>
  requisitar<Sessao>("/sessao/bloquear", { method: "POST" });

export type EstadoCadastro =
  | "sem_rosto"
  | "varios_rostos"
  | "longe"
  | "capturada"
  | "concluido";

export type Amostra = {
  estado: EstadoCadastro;
  capturadas: number;
  necessarias: number;
  rostos: Retangulo[];
};

// Manda uma foto para virar amostra do rosto de `nome`. Quem decide se a foto
// serve é o backend, igual ao desbloqueio (decisão 0011).
export const enviarAmostra = (nome: string, jpeg: Blob) =>
  requisitar<Amostra>(`/cadastro/${encodeURIComponent(nome)}/amostra`, {
    method: "POST",
    headers: { "Content-Type": "image/jpeg" },
    body: jpeg,
  });

// Joga fora um cadastro pela metade, quando o usuário desiste.
export const cancelarCadastro = (nome: string) =>
  requisitar<{ havia: boolean }>(`/cadastro/${encodeURIComponent(nome)}`, {
    method: "DELETE",
  });

export type Gravacao = {
  arquivo: string;
  bytes: number;
};

// Manda o áudio gravado no app para o backend guardar.
export const enviarGravacao = (audio: Blob) =>
  requisitar<Gravacao>("/conversa/gravacao", {
    method: "POST",
    headers: { "Content-Type": audio.type || "audio/webm" },
    body: audio,
  });

export const enviarQuadro = (jpeg: Blob) =>
  requisitar<Avaliacao>("/desbloqueio/quadro", {
    method: "POST",
    headers: { "Content-Type": "image/jpeg" },
    body: jpeg,
  });
