import { useRef, useState } from "react";
import { cancelarCadastro, enviarAmostra, type Amostra } from "../api";
import { aparencia, nomeInvalido } from "../cadastro";
import { useCamera } from "../hooks/useCamera";
import { capturar } from "../quadro";

type Props = {
  onFechar: () => void;
  onCadastrado: (nome: string) => void;
};

export function TelaCadastro({ onFechar, onCadastrado }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(document.createElement("canvas"));
  const camera = useCamera(videoRef);

  const [nome, setNome] = useState("");
  const [amostra, setAmostra] = useState<Amostra | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [capturando, setCapturando] = useState(false);

  const concluido = amostra?.estado === "concluido";
  const problemaNoNome = nomeInvalido(nome);
  // O nome não muda no meio do cadastro: as amostras já capturadas são dele.
  const nomeTravado = (amostra?.capturadas ?? 0) > 0 && !concluido;

  async function capturarAmostra() {
    const video = videoRef.current;
    if (!video || problemaNoNome) return;
    setCapturando(true);
    setErro(null);
    try {
      const jpeg = await capturar(video, canvasRef.current);
      const resposta = await enviarAmostra(nome.trim(), jpeg);
      setAmostra(resposta);
      if (resposta.estado === "concluido") onCadastrado(nome.trim());
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setCapturando(false);
    }
  }

  function desistir() {
    // Avisa o backend para ele não guardar amostras de um cadastro abandonado.
    if (nomeTravado) cancelarCadastro(nome.trim()).catch(() => {});
    onFechar();
  }

  const visual = amostra
    ? aparencia(amostra.estado, amostra.capturadas, amostra.necessarias)
    : null;
  const mensagem = (() => {
    if (camera.estado === "erro") return camera.mensagem;
    if (camera.estado === "iniciando") return "Ligando a câmera...";
    if (erro) return erro;
    if (problemaNoNome && !amostra) return problemaNoNome;
    return visual?.mensagem ?? "Olhe para a câmera e capture";
  })();
  const tom = camera.estado === "erro" || erro ? "erro" : (visual?.tom ?? "aviso");

  return (
    <div className="cadastro" role="dialog" aria-label="Cadastrar rosto">
      <div className="cadastro__caixa">
        <h2 className="cadastro__titulo">Cadastrar rosto</h2>

        <video ref={videoRef} className="cadastro__video" autoPlay playsInline muted />

        <label className="cadastro__campo">
          Nome
          <input
            className="cadastro__entrada"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            disabled={nomeTravado || concluido}
            placeholder="benedito"
            autoFocus
          />
        </label>

        <p className={`cadastro__mensagem cadastro__mensagem--${tom}`} role="status">
          {mensagem}
        </p>

        <div className="progresso" aria-hidden="true">
          <div
            className="progresso__barra"
            style={{
              width: `${((amostra?.capturadas ?? 0) / (amostra?.necessarias ?? 5)) * 100}%`,
            }}
          />
        </div>

        <div className="cadastro__acoes">
          <button className="botao" type="button" onClick={desistir}>
            {concluido ? "Fechar" : "Cancelar"}
          </button>
          {!concluido && (
            <button
              className="botao botao--destaque"
              type="button"
              onClick={capturarAmostra}
              disabled={capturando || !!problemaNoNome || camera.estado !== "ligada"}
            >
              {capturando ? "Capturando..." : "Capturar"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
