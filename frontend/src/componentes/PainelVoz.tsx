import { aparencia, type EstadoGravacao } from "../gravacao";

type Props = {
  gravacao: EstadoGravacao;
};

export function PainelVoz({ gravacao }: Props) {
  const visual = aparencia(gravacao);
  const gravando = gravacao.estado === "gravando";

  return (
    <section className="painel painel--voz">
      <h2 className="painel__titulo">Voz</h2>
      <div className="voz">
        <span className={`voz__ponto ${gravando ? "voz__ponto--gravando" : ""}`} aria-hidden="true" />
        <p className={`voz__mensagem voz__mensagem--${visual.tom}`} role="status">
          {visual.mensagem}
        </p>
      </div>
    </section>
  );
}
