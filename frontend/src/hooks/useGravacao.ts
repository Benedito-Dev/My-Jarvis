import { useEffect, useRef, useState } from "react";
import { enviarGravacao } from "../api";
import { escolherFormato, type EstadoGravacao } from "../gravacao";

/**
 * Grava a voz enquanto a barra de espaço fica segurada e manda ao backend ao soltar.
 *
 * O microfone é ligado no momento de falar e desligado ao soltar a tecla: o app
 * nunca fica escutando sozinho.
 */
export function useGravacao(ligado: boolean): EstadoGravacao {
  const [gravacao, setGravacao] = useState<EstadoGravacao>({ estado: "parado" });
  const gravador = useRef<MediaRecorder | null>(null);
  const segurando = useRef(false);

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

      const pedacos: Blob[] = [];
      const gravandoAgora = new MediaRecorder(fluxo, { mimeType: formato });
      gravandoAgora.ondataavailable = (evento) => {
        if (evento.data.size > 0) pedacos.push(evento.data);
      };
      gravandoAgora.onstop = async () => {
        fluxo.getTracks().forEach((t) => t.stop()); // desliga o microfone
        gravador.current = null;
        const audio = new Blob(pedacos, { type: formato });
        if (audio.size === 0) {
          setGravacao({ estado: "erro", mensagem: "Não saiu áudio nenhum. Tente de novo." });
          return;
        }
        setGravacao({ estado: "enviando" });
        try {
          const guardada = await enviarGravacao(audio);
          if (ativo) setGravacao({ estado: "guardada", arquivo: guardada.arquivo });
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

  return gravacao;
}

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
