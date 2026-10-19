import { type RefObject, useEffect, useRef, useState } from "react";
import { enviarGravacao } from "../api";
import { escolherFormato, type EstadoGravacao } from "../gravacao";
import { nivelDoSinal } from "../nucleo";

// Tempo mínimo do estado "pensando" (roxo) depois de soltar o ESPAÇO.
const PENSANDO_MINIMO_MS = 600;
// Quanto tempo o "Você disse" fica na tela antes de voltar a "À sua disposição".
const RECADO_MS = 6000;

export type Gravacao = {
  gravacao: EstadoGravacao;
  /** Volume da voz agora, de 0 a 1. Ref, e não estado: muda a cada quadro. */
  nivel: RefObject<number>;
};

/**
 * Grava a voz enquanto a barra de espaço fica segurada e manda ao backend ao soltar.
 *
 * O microfone é ligado no momento de falar e desligado ao soltar a tecla: o app
 * nunca fica escutando sozinho.
 */
export function useGravacao(ligado: boolean): Gravacao {
  const [gravacao, setGravacao] = useState<EstadoGravacao>({ estado: "parado" });
  const gravador = useRef<MediaRecorder | null>(null);
  const segurando = useRef(false);
  const nivel = useRef(0);

  useEffect(() => {
    if (!ligado) return;
    let ativo = true;

    async function comecar() {
      if (gravador.current || !ativo) return;
      if (typeof MediaRecorder === "undefined") {
        setGravacao({ estado: "erro", mensagem: "Este sistema não sabe gravar áudio." });
        return;
      }
      const formato = escolherFormato(MediaRecorder.isTypeSupported);
      if (!formato) {
        setGravacao({ estado: "erro", mensagem: "Nenhum formato de áudio suportado aqui." });
        return;
      }

      let fluxo: MediaStream;
      try {
        fluxo = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch (erro) {
        setGravacao({ estado: "erro", mensagem: descreverErro(erro) });
        return;
      }
      // A tecla pode ter sido solta enquanto o microfone ligava.
      if (!ativo || !segurando.current) {
        fluxo.getTracks().forEach((t) => t.stop());
        return;
      }

      const pararMedidor = medirVolume(fluxo, nivel);
      const pedacos: Blob[] = [];
      const gravandoAgora = new MediaRecorder(fluxo, { mimeType: formato });
      gravandoAgora.ondataavailable = (evento) => {
        if (evento.data.size > 0) pedacos.push(evento.data);
      };
      gravandoAgora.onstop = async () => {
        pararMedidor();
        fluxo.getTracks().forEach((t) => t.stop()); // desliga o microfone
        gravador.current = null;
        const audio = new Blob(pedacos, { type: formato });
        if (audio.size === 0) {
          setGravacao({ estado: "erro", mensagem: "Não saiu áudio nenhum. Tente de novo." });
          return;
        }
        setGravacao({ estado: "enviando" });
        try {
          // Transcrever já leva o seu tempo; o mínimo só evita o roxo piscar
          // quando a fala é curtinha.
          const [ouvida] = await Promise.all([enviarGravacao(audio), esperar(PENSANDO_MINIMO_MS)]);
          if (ativo) setGravacao({ estado: "ouvida", texto: ouvida.texto });
        } catch (erro) {
          if (ativo) setGravacao({ estado: "erro", mensagem: descreverErro(erro) });
        }
      };

      gravador.current = gravandoAgora;
      gravandoAgora.start();
      setGravacao({ estado: "gravando" });
    }

    function parar() {
      gravador.current?.stop(); // o resto acontece no onstop
    }

    function aoApertar(evento: KeyboardEvent) {
      if (evento.code !== "Space" || evento.repeat || digitando(evento.target)) return;
      evento.preventDefault(); // sem isso o espaço rola a tela e aperta o botão focado
      if (segurando.current) return;
      segurando.current = true;
      comecar();
    }

    function aoSoltar(evento: KeyboardEvent) {
      if (evento.code !== "Space" || !segurando.current) return;
      evento.preventDefault();
      segurando.current = false;
      parar();
    }

    window.addEventListener("keydown", aoApertar);
    window.addEventListener("keyup", aoSoltar);
    return () => {
      ativo = false;
      segurando.current = false;
      window.removeEventListener("keydown", aoApertar);
      window.removeEventListener("keyup", aoSoltar);
      parar();
    };
  }, [ligado]);

  // "Você disse" é um recado, não um estado: some sozinho e o Jarvis volta a
  // ficar à disposição.
  useEffect(() => {
    if (gravacao.estado !== "ouvida") return;
    const temporizador = setTimeout(() => setGravacao({ estado: "parado" }), RECADO_MS);
    return () => clearTimeout(temporizador);
  }, [gravacao]);

  return { gravacao, nivel };
}

/**
 * Mede o volume do microfone a cada quadro e guarda em `nivel`, para o núcleo
 * do painel reagir à voz. Devolve a função que para de medir.
 */
function medirVolume(fluxo: MediaStream, nivel: { current: number }): () => void {
  let contexto: AudioContext;
  try {
    contexto = new AudioContext();
  } catch {
    return () => {}; // sem Web Audio, o núcleo só não reage ao volume
  }
  // O WebKit cria o contexto pausado quando não nasce de um clique: sem isto o
  // analisador só mede silêncio e o núcleo fica parado.
  if (contexto.state === "suspended") contexto.resume();
  const analisador = contexto.createAnalyser();
  analisador.fftSize = 512;
  contexto.createMediaStreamSource(fluxo).connect(analisador);
  const amostras = new Uint8Array(analisador.fftSize);

  let quadro = 0;
  const medir = () => {
    analisador.getByteTimeDomainData(amostras);
    nivel.current = nivelDoSinal(amostras);
    quadro = requestAnimationFrame(medir);
  };
  medir();

  return () => {
    cancelAnimationFrame(quadro);
    nivel.current = 0;
    contexto.close();
  };
}

const esperar = (ms: number) => new Promise((resolver) => setTimeout(resolver, ms));

function digitando(alvo: EventTarget | null): boolean {
  const elemento = alvo as HTMLElement | null;
  const etiqueta = elemento?.tagName;
  return etiqueta === "INPUT" || etiqueta === "TEXTAREA" || !!elemento?.isContentEditable;
}

function descreverErro(erro: unknown): string {
  if (erro instanceof DOMException && erro.name === "NotAllowedError") {
    return "Sem permissão de microfone. Libere o acesso nas configurações do sistema.";
  }
  if (erro instanceof DOMException && erro.name === "NotFoundError") {
    return "Nenhum microfone encontrado.";
  }
  return erro instanceof Error ? erro.message : String(erro);
}
