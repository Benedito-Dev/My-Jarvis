import type { EventoConversa } from "./gravacao";
import { LeitorDeLinhas } from "./linhas";
import type { EventoVoz } from "./voz";

// Ponte com o backend Python (jarvis servidor), que roda só nesta máquina.
export const URL_BACKEND = "http://127.0.0.1:8765";

// Quanto o app espera o backend responder. Curto, para perceber logo se ele caiu.
const TEMPO_LIMITE_MS = 2000;
// Transcrever a voz é trabalho pesado: numa máquina ocupada leva vários segundos.
const TEMPO_LIMITE_TRANSCRICAO_MS = 60_000;

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

async function requisitar<T>(
  caminho: string,
  opcoes: RequestInit = {},
  tempoLimite = TEMPO_LIMITE_MS,
): Promise<T> {
  const resposta = await fetch(`${URL_BACKEND}${caminho}`, {
    ...opcoes,
    signal: AbortSignal.timeout(tempoLimite),
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

export type Lembrete = {
  id: number;
  texto: string;
  /** Quando toca, em ISO 8601. */
  quando: string;
};

// Só vêm com o Jarvis desbloqueado; bloqueado, o backend devolve a lista vazia.
export const buscarLembretes = () => requisitar<Lembrete[]>("/lembretes");

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

/**
 * Manda o áudio gravado e recebe a conversa EM FLUXO: cada evento (o que foi
 * dito, cada frase da resposta, o fim) chega assim que o backend o tem, em vez
 * de esperar a resposta inteira. Ver `/conversa/gravacao` no backend.
 */
export async function conversar(
  audio: Blob,
  aoEvento: (evento: EventoConversa) => void,
  chamado = false,
): Promise<void> {
  // `chamado`: veio da escuta (o nome, sem tecla). O backend confere se era mesmo.
  const rota = chamado ? "/conversa/gravacao?chamado=true" : "/conversa/gravacao";
  const resposta = await fetch(`${URL_BACKEND}${rota}`, {
    method: "POST",
    headers: { "Content-Type": audio.type || "audio/webm" },
    body: audio,
    signal: AbortSignal.timeout(TEMPO_LIMITE_TRANSCRICAO_MS),
  });
  await lerConversa(resposta, aoEvento);
}

/** O mesmo que `conversar`, com um texto digitado no lugar da voz (sem transcrição). */
export async function conversarPorTexto(
  texto: string,
  aoEvento: (evento: EventoConversa) => void,
): Promise<void> {
  const resposta = await fetch(`${URL_BACKEND}/conversa/texto`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto }),
    signal: AbortSignal.timeout(TEMPO_LIMITE_TRANSCRICAO_MS),
  });
  await lerConversa(resposta, aoEvento);
}

/**
 * Fica ouvindo o canal da voz do Jarvis (uma linha por fala que começa) até o
 * `sinal` cancelar ou o backend fechar. Não tem tempo limite: é um canal aberto.
 */
export async function ouvirVozDoJarvis(
  aoEvento: (evento: EventoVoz) => void,
  sinal: AbortSignal,
): Promise<void> {
  const resposta = await fetch(`${URL_BACKEND}/voz/eventos`, { signal: sinal });
  await lerLinhas(resposta, (linha) => aoEvento(JSON.parse(linha)));
}

async function lerConversa(
  resposta: Response,
  aoEvento: (evento: EventoConversa) => void,
): Promise<void> {
  if (!resposta.ok || !resposta.body) {
    const corpo = await resposta.json().catch(() => null);
    throw new Error(corpo?.detail ?? `Backend respondeu ${resposta.status} na conversa`);
  }
  await lerLinhas(resposta, (linha) => aoEvento(JSON.parse(linha)));
}

/** Lê um corpo em fluxo, linha por linha, conforme os bytes chegam. */
async function lerLinhas(resposta: Response, aoLer: (linha: string) => void): Promise<void> {
  if (!resposta.body) throw new Error("Resposta sem corpo");
  const leitor = resposta.body.getReader();
  const decodificador = new TextDecoder();
  const linhas = new LeitorDeLinhas();
  for (;;) {
    const { done, value } = await leitor.read();
    if (done) break;
    linhas.empurrar(decodificador.decode(value, { stream: true })).forEach(aoLer);
  }
  linhas.terminar().forEach(aoLer);
}

export const enviarQuadro = (jpeg: Blob) =>
  requisitar<Avaliacao>("/desbloqueio/quadro", {
    method: "POST",
    headers: { "Content-Type": "image/jpeg" },
    body: jpeg,
  });
