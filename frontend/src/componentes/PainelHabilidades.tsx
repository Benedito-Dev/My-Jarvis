import type { Habilidade } from "../api";

export function PainelHabilidades({ habilidades }: { habilidades: Habilidade[] }) {
  return (
    <section className="painel">
      <h2 className="painel__titulo">Habilidades</h2>
      <ul className="lista">
        {habilidades.map((habilidade) => (
          <li key={habilidade.id} className={`item item--${habilidade.situacao}`}>
            <span className="item__icone" aria-hidden="true">
              {habilidade.situacao === "pronta" ? "✓" : "⋯"}
            </span>
            <div>
              <strong>{habilidade.nome}</strong>
              {habilidade.situacao === "em_breve" && <span className="selo">em breve</span>}
              <p>{habilidade.descricao}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
