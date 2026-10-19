import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { desbloquearPorPin } from "../api";
import { aparencia } from "../desbloqueio";
import { Abertura, DURACAO_ABERTURA_MS } from "./Abertura";
import { AneisHud } from "./AneisHud";
import { LeiturasHud } from "./LeiturasHud";
import { Scanner } from "./Scanner";
import { useCamera } from "../hooks/useCamera";
import { useDesbloqueio } from "../hooks/useDesbloqueio";
import { useRelogio } from "../hooks/useRelogio";
import { LARGURA_QUADRO } from "../quadro";

const DURACAO_BOAS_VINDAS_MS = 2500;

type Props = {
  nomeAssistente: string;
  backendOnline: boolean;
  onDesbloqueado: (usuario: string) => void;
};

type ModoAcesso = "facial" | "pin";

export function TelaBloqueio({ nomeAssistente, backendOnline, onDesbloqueado }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const agora = useRelogio();
  const [modo, setModo] = useState<ModoAcesso>("facial");
  const [abrindo, setAbrindo] = useState(true);
  const [identificador, setIdentificador] = useState("");
  const [pin, setPin] = useState("");
  const [pinErro, setPinErro] = useState<string | null>(null);
  const [enviandoPin, setEnviandoPin] = useState(false);
  const [animandoPin, setAnimandoPin] = useState(false);
  const transicaoPinRef = useRef<number | null>(null);

  useEffect(() => {
    const temporizador = setTimeout(() => setAbrindo(false), DURACAO_ABERTURA_MS);
    return () => clearTimeout(temporizador);
  }, []);

  useEffect(() => {
    return () => {
      if (transicaoPinRef.current !== null) window.clearTimeout(transicaoPinRef.current);
    };
  }, []);

  const camera = useCamera(videoRef, modo === "facial");
  const { avaliacao, erro, altura } = useDesbloqueio(
    videoRef,
    modo === "facial" && camera.estado === "ligada" && backendOnline,
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

  const abrirPin = useCallback(() => {
    setModo("pin");
    setPinErro(null);
    setAbrindo(false);
    setAnimandoPin(true);
    if (transicaoPinRef.current !== null) window.clearTimeout(transicaoPinRef.current);
    transicaoPinRef.current = window.setTimeout(() => {
      setAnimandoPin(false);
      transicaoPinRef.current = null;
    }, 900);
  }, []);

  useEffect(() => {
    if (modo !== "facial") return;

    function lidarComTecla(evento: KeyboardEvent) {
      if (evento.key !== "ArrowDown" || evento.repeat || evento.altKey || evento.ctrlKey || evento.metaKey) {
        return;
      }

      evento.preventDefault();
      abrirPin();
    }

    window.addEventListener("keydown", lidarComTecla);
    return () => window.removeEventListener("keydown", lidarComTecla);
  }, [abrirPin, modo]);

  function voltarParaRosto() {
    setModo("facial");
    setPinErro(null);
    setPin("");
  }

  async function enviarPin(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!backendOnline || identificador.trim().length < 3 || pin.length !== 6) return;

    setEnviandoPin(true);
    setPinErro(null);
    try {
      const sessao = await desbloquearPorPin(identificador, pin);
      if (sessao.usuario) onDesbloqueado(sessao.usuario);
    } catch (erroPin) {
      setPinErro(erroPin instanceof Error ? erroPin.message : "Identificador ou PIN inválido.");
    } finally {
      setEnviandoPin(false);
    }
  }

  return (
    <div className={`bloqueio bloqueio--${modo}${animandoPin ? " bloqueio--transicionando" : ""}`}>
      {animandoPin && (
        <div className="pin-transicao" aria-hidden="true">
          <div className="pin-transicao__linha pin-transicao__linha--uma" />
          <div className="pin-transicao__linha pin-transicao__linha--duas" />
          <div className="pin-transicao__nucleo" />
          <span className="pin-transicao__codigo">ACCESS CHANNEL / PIN</span>
        </div>
      )}
      {modo === "facial" && abrindo && <Abertura nomeAssistente={nomeAssistente} />}

      <div className="bloqueio__topo">
        <span className={`reator ${backendOnline ? "" : "reator--desconectado"}`} aria-hidden="true" />
        {nomeAssistente} · {modo === "pin" ? "ACESSO ALTERNATIVO" : "BLOQUEADO"}
      </div>

      {modo === "facial" ? (
        <>
          <div className={`visor visor--${tom}`}>
            <div className="visor__janela">
              <video ref={videoRef} className="visor__video" autoPlay playsInline muted />
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
            <button
              className="bloqueio__alternativa bloqueio__alternativa--seta"
              type="button"
              onClick={abrirPin}
              aria-label="Abrir acesso alternativo por identificador e PIN"
              aria-keyshortcuts="ArrowDown"
              title="Usar identificador e PIN"
            >
              <span className="bloqueio__seta-circulo" aria-hidden="true">
                <svg className="bloqueio__seta-icone" viewBox="0 0 24 24">
                  <path d="M12 6v12M7.5 13.5 12 18l4.5-4.5" />
                </svg>
              </span>
              <span className="bloqueio__seta-legenda" aria-hidden="true">
                <strong>Usar PIN sem câmera</strong>
                <small>Pressione ↓ ou clique</small>
              </span>
              <span className="bloqueio__seta-acento" aria-hidden="true" />
            </button>
          </div>
        </>
      ) : (
        <section className="acesso-pin" aria-labelledby="acesso-pin-titulo">
          <div className="acesso-pin__sinal" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
          <p className="acesso-pin__eyebrow">MÉTODO ALTERNATIVO · SEM CÂMERA</p>
          <h1 id="acesso-pin-titulo">Entrar com PIN</h1>
          <p className="acesso-pin__descricao">
            Digite seu identificador. O Jarvis não exibe nem sugere perfis cadastrados.
          </p>

          <form className="acesso-pin__formulario" onSubmit={enviarPin}>
            <label className="acesso-pin__campo">
              <span>Identificador</span>
              <input
                value={identificador}
                onChange={(evento) => setIdentificador(evento.target.value)}
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="seu identificador"
                autoFocus
                disabled={enviandoPin}
              />
            </label>
            <label className="acesso-pin__campo">
              <span>PIN de 6 dígitos</span>
              <input
                value={pin}
                onChange={(evento) => setPin(evento.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric"
                autoComplete="current-password"
                type="password"
                placeholder="••••••"
                maxLength={6}
                disabled={enviandoPin}
              />
            </label>

            {pinErro && <p className="acesso-pin__erro" role="alert">{pinErro}</p>}
            {!backendOnline && (
              <p className="acesso-pin__erro" role="alert">
                O backend está offline. Inicie o servidor para autenticar.
              </p>
            )}

            <button
              className="acesso-pin__entrar"
              type="submit"
              disabled={
                enviandoPin || !backendOnline || identificador.trim().length < 3 || pin.length !== 6
              }
            >
              {enviandoPin ? "Verificando…" : "Desbloquear Jarvis"}
            </button>
          </form>

          <button className="bloqueio__alternativa" type="button" onClick={voltarParaRosto}>
            Voltar ao reconhecimento facial
          </button>
        </section>
      )}
    </div>
  );
}
