import type { Cartao } from "./cartoes";
import type { Tom } from "./desbloqueio";

/** Um evento do fluxo da conversa, como o backend manda (uma linha NDJSON cada). */
export type EventoConversa =
  | { tipo: "ouvido"; texto: string; arquivo: string }
  | { tipo: "trecho"; texto: string }
  | { tipo: "usando"; ferramenta: string }
  | { tipo: "cartao"; cartao: Cartao }
  | { tipo: "fim"; acao: string | null };

export type EstadoGravacao =
  | { estado: "parado" }
  | { estado: "gravando" }
  | { estado: "enviando" }
  | {
      estado: "ouvida";
      texto: string;
      /** A resposta do Jarvis, crescendo frase a frase enquanto ele fala. */
      resposta: string;
      acao: string | null;
      /** O backend mandou o "fim": a resposta está completa. */
      terminou: boolean;
      /** O que as ferramentas trouxeram nesta conversa, para mostrar na tela. */
      cartoes: Cartao[];
      /** A ferramenta rodando agora (ex.: "clima"), ou null. */
      usando: string | null;
      /** Quantos trechos da resposta já chegaram. */
      trechos: number;
      /** Para cada cartão, quantos trechos tinham chegado antes dele: o cartão
       * é sobre a fala seguinte e só aparece quando ela começa a tocar. */
      falaDoCartao: number[];
    }
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
      // O backend está transcrevendo (Whisper); depois, também pensará na resposta.
      return { titulo: "Pensando", detalhe: "Entendendo o que você disse...", tom: "pensando" };
    case "ouvida":
      // Azul de novo: verde é só enquanto está ouvindo.
      if (!gravacao.texto) {
        return { titulo: "Não entendi", detalhe: "Fale um pouco mais perto do microfone", tom: "aviso" };
      }
      // Já sabe o que foi dito, mas a resposta ainda não começou: segue pensando (roxo).
      return {
        titulo: "Você disse",
        detalhe: `“${gravacao.texto}”`,
        tom: gravacao.resposta || gravacao.terminou ? "aviso" : "pensando",
      };
    case "erro":
      return { titulo: "Não consegui ouvir", detalhe: gravacao.mensagem, tom: "erro" };
  }
}

// A voz Faber (Piper) fala ~15 letras por segundo (medido: 98 letras em 6,6 s);
// mais um respiro para começar.
const MS_POR_LETRA_FALADA = 67;
const MS_PARA_COMECAR_A_FALAR = 300;

/**
 * Quanto tempo, mais ou menos, o Jarvis leva para falar a frase. O app não
 * ouve a voz do backend, então estima pelo tamanho: serve para o núcleo
 * "falar" junto, não para cronometrar nada.
 */
export function duracaoDaFala(frase: string): number {
  return MS_PARA_COMECAR_A_FALAR + frase.length * MS_POR_LETRA_FALADA;
}

/** Aplica um evento do fluxo ao estado da conversa (lógica pura, testável). */
export function aplicarEvento(atual: EstadoGravacao, evento: EventoConversa): EstadoGravacao {
  switch (evento.tipo) {
    case "ouvido":
      return {
        estado: "ouvida",
        texto: evento.texto,
        resposta: "",
        acao: null,
        terminou: false,
        cartoes: [],
        usando: null,
        trechos: 0,
        falaDoCartao: [],
      };
    case "trecho":
      if (atual.estado !== "ouvida") return atual;
      return {
        ...atual,
        resposta: atual.resposta ? `${atual.resposta} ${evento.texto}` : evento.texto,
        trechos: atual.trechos + 1,
      };
    case "usando":
      if (atual.estado !== "ouvida") return atual;
      return { ...atual, usando: evento.ferramenta };
    case "cartao":
      if (atual.estado !== "ouvida") return atual;
      return {
        ...atual,
        cartoes: [...atual.cartoes, evento.cartao],
        falaDoCartao: [...atual.falaDoCartao, atual.trechos],
        usando: null,
      };
    case "fim":
      if (atual.estado !== "ouvida") return atual;
      return { ...atual, acao: evento.acao, terminou: true, usando: null };
  }
}

/** O que o painel mostra na manchete (e o que decide onde ficam os cartões). */
export type FasePainel = "espera" | "ouvindo" | "pensando" | "falando";

/**
 * A fase do painel. `falando` já deve vir com folga (useSustentado): entre duas
 * frases a voz para um instante, e isso não pode virar "em espera". Enquanto a
 * conversa não terminou, o que não é fala é "pensando". `aguardandoVoz`: a
 * resposta chegou inteira, mas a voz ainda não começou.
 */
export function faseDoPainel(
  gravacao: EstadoGravacao,
  falando: boolean,
  aguardandoVoz = false,
): FasePainel {
  if (gravacao.estado === "gravando") return "ouvindo";
  if (falando) return "falando";
  // A resposta já chegou, mas a voz ainda está sendo gerada: ainda não acabou.
  if (aguardandoVoz) return "pensando";
  if (gravacao.estado === "enviando") return "pensando";
  if (gravacao.estado === "ouvida" && !gravacao.terminou) return "pensando";
  return "espera";
}

/** Uma troca concluída da conversa, para o histórico na tela. */
export type Troca = { id: number; pergunta: string; resposta: string; quando: Date };

/**
 * Se a conversa acabou de terminar (com algo dito), devolve o histórico com ela
 * no fim; senão, o mesmo histórico. Guarda as `maximo` mais recentes.
 */
export function registrarTroca(
  historico: Troca[],
  gravacao: EstadoGravacao,
  quando: Date,
  maximo = 30,
): Troca[] {
  if (gravacao.estado !== "ouvida" || !gravacao.terminou || !gravacao.texto) return historico;
  const id = (historico[historico.length - 1]?.id ?? 0) + 1;
  const troca = { id, pergunta: gravacao.texto, resposta: gravacao.resposta, quando };
  return [...historico, troca].slice(-maximo);
}
