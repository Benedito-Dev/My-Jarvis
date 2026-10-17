import { useEffect, useRef } from "react";
import { aparencia } from "../desbloqueio";
import { useCamera } from "../hooks/useCamera";
import { useDesbloqueio } from "../hooks/useDesbloqueio";
import { LARGURA_QUADRO } from "../quadro";

// Quanto tempo o "Bem-vindo" fica na tela antes de entrar.
const DURACAO_BOAS_VINDAS_MS = 2500;

type Props = {
  nomeAssistente: string;
  backendOnline: boolean;
  onDesbloqueado: (usuario: string) => void;
};

export function TelaBloqueio({ nomeAssistente, backendOnline, onDesbloqueado }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const camera = useCamera(videoRef);
  const { avaliacao, erro, altura } = useDesbloqueio(
    videoRef,
    camera.estado === "ligada" && backendOnline,
  );

  const usuario = avaliacao?.estado === "desbloqueado" ? avaliacao.usuario : null;
  useEffect(() => {
    if (!usuario) return;
    const temporizador = setTimeout(() => onDesbloqueado(usuario), DURACAO_BOAS_VINDAS_MS);
    return () => clearTimeout(temporizador);
  }, [usuario, onDesbloqueado]);

  const visual = avaliacao ? aparencia(avaliacao.estado, avaliacao.usuario) : null;
  const mensagem = (() => {
    if (camera.estado === "erro") return camera.mensagem;
    if (camera.estado === "iniciando") return "Ligando a câmera...";
    if (!backendOnline) return "Backend desconectado. Rode: uv run python -m jarvis servidor";
    if (erro) return erro;
    return visual?.mensagem ?? "Por favor, aproxime seu rosto";
  })();
  const tom = camera.estado === "erro" || !backendOnline || erro ? "erro" : (visual?.tom ?? "aviso");

  return (
    <div className="bloqueio">
      <video ref={videoRef} className="bloqueio__video" autoPlay playsInline muted />

      {/* Mesma proporção e corte do vídeo (object-fit: cover = slice), e também espelhado */}
      <svg
        className="bloqueio__marcacoes"
        viewBox={`0 0 ${LARGURA_QUADRO} ${altura}`}
        preserveAspectRatio="xMidYMid slice"
        aria-hidden="true"
      >
        {avaliacao?.rostos.map((rosto, indice) => (
          <rect
            key={indice}
            className={`marcacao marcacao--${visual?.tom}`}
            x={rosto.esquerda}
            y={rosto.topo}
            width={rosto.direita - rosto.esquerda}
            height={rosto.base - rosto.topo}
            rx={8}
          />
        ))}
      </svg>

      <div className="bloqueio__sobreposicao">
        <div className="bloqueio__topo">
          <span
            className={`reator ${usuario ? "" : "reator--desconectado"}`}
            aria-hidden="true"
          />
          {nomeAssistente} · {usuario ? "DESBLOQUEADO" : "BLOQUEADO"}
        </div>

        <div className="bloqueio__rodape">
          <p className={`bloqueio__mensagem bloqueio__mensagem--${tom}`} role="status">
            {mensagem}
          </p>
          <div className="progresso" aria-hidden="true">
            <div
              className="progresso__barra"
              style={{ width: `${(avaliacao?.progresso ?? 0) * 100}%` }}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
