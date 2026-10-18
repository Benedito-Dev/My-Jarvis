import { useEffect, useRef, useState } from "react";
import { aparencia } from "../desbloqueio";
import { Abertura, DURACAO_ABERTURA_MS } from "./Abertura";
import { useCamera } from "../hooks/useCamera";
import { useRelogio } from "../hooks/useRelogio";
import { useDesbloqueio } from "../hooks/useDesbloqueio";
import { LARGURA_QUADRO } from "../quadro";
import { AneisHud } from "./AneisHud";
import { LeiturasHud } from "./LeiturasHud";
import { Scanner } from "./Scanner";

// Quanto tempo o "Bem-vindo" fica na tela antes de entrar.
const DURACAO_BOAS_VINDAS_MS = 2500;

type Props = {
  nomeAssistente: string;
  backendOnline: boolean;
  onDesbloqueado: (usuario: string) => void;
};

export function TelaBloqueio({ nomeAssistente, backendOnline, onDesbloqueado }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);

  // A abertura roda uma vez por entrada na tela e depois sai do caminho.
  const [abrindo, setAbrindo] = useState(true);
  useEffect(() => {
    const temporizador = setTimeout(() => setAbrindo(false), DURACAO_ABERTURA_MS);
    return () => clearTimeout(temporizador);
  }, []);

  const camera = useCamera(videoRef);
  const agora = useRelogio();
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
    return visual?.mensagem ?? "Posicione o rosto no círculo";
  })();
  const tom = camera.estado === "erro" || !backendOnline || erro ? "erro" : (visual?.tom ?? "aviso");

  return (
    <div className="bloqueio">
      {abrindo && <Abertura nomeAssistente={nomeAssistente} />}

      <div className="bloqueio__topo">
        <span className={`reator ${usuario ? "" : "reator--desconectado"}`} aria-hidden="true" />
        {nomeAssistente} · {usuario ? "DESBLOQUEADO" : "BLOQUEADO"}
      </div>

      {/* O visor: a câmera só aparece dentro do círculo, e é ali que o rosto vai. */}
      <div className={`visor visor--${tom}`}>
        <div className="visor__janela">
          <video ref={videoRef} className="visor__video" autoPlay playsInline muted />

          {/* Mesma proporção e corte do vídeo (object-fit: cover = slice), e também espelhado */}
          <svg
            className="visor__marcacoes"
            viewBox={`0 0 ${LARGURA_QUADRO} ${altura}`}
            preserveAspectRatio="xMidYMid slice"
            aria-hidden="true"
          >
            <Scanner rostos={avaliacao?.rostos ?? []} tom={tom} />
          </svg>
        </div>

        <AneisHud progresso={avaliacao?.progresso ?? 0} />
      </div>

      <LeiturasHud
        backendOnline={backendOnline}
        cameraLigada={camera.estado === "ligada"}
        rostosNaTela={avaliacao?.rostos.length ?? 0}
        progresso={avaliacao?.progresso ?? 0}
        agora={agora}
      />

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
  );
}
