import { useCallback, useEffect, useRef, useState } from "react";
import { URL_BACKEND } from "../api";
import { MemoriaDeSom, Pedido, reamostrar, wav } from "../escuta";

// A escuta sem tecla (decisão 0023): com ela ligada, o microfone fica aberto e
// o som vai, em 16 kHz, para o backend, que avisa quando ouviu "Jarvis". Aí o
// app grava o pedido (com o "Jarvis" que já passou) até a pessoa parar de falar.
// Quem confirma se foi mesmo um chamado é o backend, transcrevendo.

const URL_ESCUTA = `${URL_BACKEND.replace(/^http/, "ws")}/escuta`;
const ESPERA_PARA_RECONECTAR_MS = 3000;
const CHAVE_LIGADA = "jarvis.escuta";

export type EstadoEscuta = "desligada" | "ligando" | "ouvindo" | "indisponivel" | "erro";

/** O que a escuta está gravando agora: um possível chamado, ou o pedido depois do "Pois não?". */
export type Atencao = "chamado" | "pedido" | null;

export type Escuta = {
  estado: EstadoEscuta;
  /** Por que está indisponível ou deu erro. */
  motivo: string | null;
  atencao: Atencao;
  ligada: boolean;
  alternar: () => void;
  /** Grava o próximo pedido sem precisar do nome (depois do "Pois não?"). */
  escutarAgora: () => void;
};

// Junta o som do microfone em pedaços de ~40 ms e manda para a página.
const COLETOR = `
class ColetorJarvis extends AudioWorkletProcessor {
  constructor() { super(); this.pedacos = []; this.total = 0; }
  process(entradas) {
    const canal = entradas[0] && entradas[0][0];
    if (canal) {
      this.pedacos.push(canal.slice());
      this.total += canal.length;
      if (this.total >= 2048) {
        const junto = new Float32Array(this.total);
        let posicao = 0;
        for (const p of this.pedacos) { junto.set(p, posicao); posicao += p.length; }
        this.port.postMessage(junto, [junto.buffer]);
        this.pedacos = []; this.total = 0;
      }
    }
    return true;
  }
}
registerProcessor("coletor-jarvis", ColetorJarvis);
`;

function lerLigada(): boolean {
  try {
    return localStorage.getItem(CHAVE_LIGADA) !== "nao";
  } catch {
    return true;
  }
}

/**
 * `podeOuvir`: sessão aberta e backend no ar. `pausada`: o Jarvis está ocupado
 * (falando, pensando ou gravando pelo ESPAÇO): não procura o nome, para não
 * acordar com a própria voz. `aoPedir` recebe o pedido gravado, em wav.
 */
export function useEscuta(
  podeOuvir: boolean,
  pausada: boolean,
  aoPedir: (audio: Blob, chamado: boolean) => void,
): Escuta {
  const [ligada, setLigada] = useState(lerLigada);
  const [estado, setEstado] = useState<EstadoEscuta>("desligada");
  const [motivo, setMotivo] = useState<string | null>(null);
  const [atencao, setAtencao] = useState<Atencao>(null);

  const pausadaRef = useRef(pausada);
  pausadaRef.current = pausada;
  const aoPedirRef = useRef(aoPedir);
  aoPedirRef.current = aoPedir;
  // O pedido sendo gravado agora, e se ele veio do nome (true) ou do "Pois não?".
  const pedido = useRef<{ gravacao: Pedido; chamado: boolean } | null>(null);
  const memoria = useRef(new MemoriaDeSom());

  const alternar = useCallback(() => {
    setLigada((atual) => {
      try {
        localStorage.setItem(CHAVE_LIGADA, atual ? "nao" : "sim");
      } catch {
        // sem armazenamento: vale só até fechar o app
      }
      return !atual;
    });
  }, []);

  const estadoRef = useRef(estado);
  estadoRef.current = estado;
  const escutarAgora = useCallback(() => {
    if (pedido.current || estadoRef.current !== "ouvindo") return;
    pedido.current = { gravacao: new Pedido(new Int16Array(0), false), chamado: false };
    setAtencao("pedido");
  }, []);

  useEffect(() => {
    if (!podeOuvir || !ligada) {
      setEstado("desligada");
      return;
    }
    let ativo = true;
    let canal: WebSocket | null = null;
    let religar = 0;
    let contexto: AudioContext | null = null;
    let fluxo: MediaStream | null = null;
    let enderecoDoColetor = "";

    function abrirCanal() {
      canal = new WebSocket(URL_ESCUTA);
      canal.binaryType = "arraybuffer";
      canal.onmessage = (mensagem) => {
        const evento = JSON.parse(String(mensagem.data));
        if (evento.tipo === "pronta") {
          setEstado("ouvindo");
          setMotivo(null);
        } else if (evento.tipo === "indisponivel") {
          setEstado("indisponivel");
          setMotivo(evento.motivo ?? null);
        } else if (evento.tipo === "jarvis" && !pausadaRef.current && !pedido.current) {
          // O nome já foi dito: o pedido começa com o som de antes.
          pedido.current = { gravacao: new Pedido(memoria.current.tudo(), true), chamado: true };
          setAtencao("chamado");
        }
      };
      canal.onclose = () => {
        if (!ativo) return;
        setEstado((atual) => (atual === "indisponivel" ? atual : "ligando"));
        religar = window.setTimeout(() => {
          if (ativo) abrirCanal();
        }, ESPERA_PARA_RECONECTAR_MS);
      };
    }

    function aoSom(entrada: Float32Array, taxa: number) {
      const pcm = reamostrar(entrada, taxa);
      memoria.current.guardar(pcm);
      const atual = pedido.current;
      if (atual) {
        if (atual.gravacao.juntar(pcm)) {
          pedido.current = null;
          memoria.current.esvaziar();
          setAtencao(null);
          if (atual.gravacao.temFala) aoPedirRef.current(wav(atual.gravacao.som()), atual.chamado);
        }
        return;
      }
      if (!pausadaRef.current && canal?.readyState === WebSocket.OPEN) canal.send(pcm);
    }

    async function ligar() {
      setEstado("ligando");
      try {
        fluxo = await navigator.mediaDevices.getUserMedia({
          // Tira o eco da própria voz do Jarvis e o ruído de fundo.
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        });
        if (!ativo) return;
        contexto = new AudioContext();
        if (contexto.state === "suspended") await contexto.resume();
        enderecoDoColetor = URL.createObjectURL(
          new Blob([COLETOR], { type: "application/javascript" }),
        );
        await contexto.audioWorklet.addModule(enderecoDoColetor);
        if (!ativo) return;
        const coletor = new AudioWorkletNode(contexto, "coletor-jarvis");
        const taxa = contexto.sampleRate;
        coletor.port.onmessage = (mensagem) => aoSom(mensagem.data as Float32Array, taxa);
        // Ligado a um volume zero: o som segue o caminho até o fim sem sair na caixa.
        const mudo = contexto.createGain();
        mudo.gain.value = 0;
        contexto.createMediaStreamSource(fluxo).connect(coletor).connect(mudo);
        mudo.connect(contexto.destination);
        abrirCanal();
      } catch (erro) {
        if (!ativo) return;
        setEstado("erro");
        setMotivo(
          erro instanceof DOMException && erro.name === "NotAllowedError"
            ? "Sem permissão de microfone."
            : erro instanceof Error
              ? erro.message
              : String(erro),
        );
      }
    }
    ligar();

    return () => {
      ativo = false;
      window.clearTimeout(religar);
      canal?.close();
      fluxo?.getTracks().forEach((t) => t.stop()); // desliga o microfone
      contexto?.close();
      if (enderecoDoColetor) URL.revokeObjectURL(enderecoDoColetor);
      pedido.current = null;
      memoria.current.esvaziar();
      setAtencao(null);
    };
  }, [podeOuvir, ligada]);

  return { estado, motivo, atencao, ligada, alternar, escutarAgora };
}
