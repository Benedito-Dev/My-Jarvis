import { useEffect, useState, type RefObject } from "react";

export type EstadoCamera =
  | { estado: "iniciando" }
  | { estado: "ligada" }
  | { estado: "erro"; mensagem: string };

// Liga a webcam e mostra no <video>. Desliga sozinha quando o componente sai da tela.
export function useCamera(videoRef: RefObject<HTMLVideoElement | null>): EstadoCamera {
  const [camera, setCamera] = useState<EstadoCamera>({ estado: "iniciando" });

  useEffect(() => {
    let fluxo: MediaStream | null = null;
    let ativo = true;

    navigator.mediaDevices
      .getUserMedia({ video: { width: 1280, height: 720, facingMode: "user" } })
      .then((recebido) => {
        if (!ativo) {
          recebido.getTracks().forEach((trilha) => trilha.stop());
          return;
        }
        fluxo = recebido;
        if (videoRef.current) videoRef.current.srcObject = recebido;
        setCamera({ estado: "ligada" });
      })
      .catch((erro: unknown) => {
        if (ativo) setCamera({ estado: "erro", mensagem: descreverErro(erro) });
      });

    return () => {
      ativo = false;
      fluxo?.getTracks().forEach((trilha) => trilha.stop());
    };
  }, [videoRef]);

  return camera;
}

function descreverErro(erro: unknown): string {
  if (erro instanceof DOMException && erro.name === "NotAllowedError") {
    return "Sem permissão de câmera. Libere o acesso à câmera nas configurações do sistema.";
  }
  if (erro instanceof DOMException && erro.name === "NotFoundError") {
    return "Nenhuma câmera encontrada.";
  }
  if (!navigator.mediaDevices) {
    return "Este app não tem acesso à API de câmera.";
  }
  return `Não consegui abrir a câmera (${erro instanceof Error ? erro.message : String(erro)}).`;
}
