import { formatarData, formatarHoraCompleta } from "../tempo";

// Barras decorativas do canto direito: nenhuma mede coisa alguma, são enfeite.
// O que é informação de verdade está nas leituras, com rótulo.
const BARRAS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11];

type Props = {
  backendOnline: boolean;
  cameraLigada: boolean;
  rostosNaTela: number;
  progresso: number;
  agora: Date;
};

/** As colunas laterais da tela de bloqueio: estado do sistema e relógio. */
export function LeiturasHud({
  backendOnline,
  cameraLigada,
  rostosNaTela,
  progresso,
  agora,
}: Props) {
  return (
    <>
      <div className="leituras leituras--esquerda">
        <h2 className="leituras__titulo">Sistema</h2>
        <Leitura rotulo="Backend" valor={backendOnline ? "ONLINE" : "OFFLINE"} ok={backendOnline} />
        <Leitura rotulo="Câmera" valor={cameraLigada ? "ATIVA" : "AGUARDE"} ok={cameraLigada} />
        <Leitura rotulo="Rostos" valor={String(rostosNaTela).padStart(2, "0")} />
        <Leitura rotulo="Leitura" valor={`${Math.round(progresso * 100)}%`} />
      </div>

      <div className="leituras leituras--direita">
        <p className="leituras__relogio">{formatarHoraCompleta(agora)}</p>
        <p className="leituras__data">{formatarData(agora)}</p>

        <div className="leituras__barras" aria-hidden="true">
          {BARRAS.map((indice) => (
            <span key={indice} style={{ animationDelay: `${indice * 0.13}s` }} />
          ))}
        </div>
      </div>
    </>
  );
}

function Leitura({ rotulo, valor, ok }: { rotulo: string; valor: string; ok?: boolean }) {
  return (
    <p className="leitura">
      <span className="leitura__rotulo">{rotulo}</span>
      <span className={`leitura__valor ${ok === false ? "leitura__valor--erro" : ""}`}>{valor}</span>
    </p>
  );
}
