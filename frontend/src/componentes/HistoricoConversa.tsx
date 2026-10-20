import { useEffect } from "react";
import type { Troca } from "../gravacao";
import { formatarHora } from "../tempo";

type Props = {
  trocas: Troca[];
  onFechar: () => void;
};

/**
 * A gaveta com a conversa desta sessão, da mais antiga à mais nova. Some ao
 * bloquear (vive no painel, que é desmontado): a próxima pessoa não a vê.
 */
export function HistoricoConversa({ trocas, onFechar }: Props) {
  useEffect(() => {
    const aoApertar = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") onFechar();
    };
    window.addEventListener("keydown", aoApertar);
    return () => window.removeEventListener("keydown", aoApertar);
  }, [onFechar]);

  return (
    <div className="historico" role="dialog" aria-label="Histórico da conversa">
      <button className="historico__fundo" type="button" onClick={onFechar} aria-label="Fechar" />
      <aside className="historico__gaveta">
        <header className="historico__cabecalho">
          <span className="modulo__indice" aria-hidden="true">
            05
          </span>
          <h2 className="historico__titulo">Conversa</h2>
          <span className="modulo__traco" aria-hidden="true" />
          <button className="historico__fechar" type="button" onClick={onFechar}>
            ESC
          </button>
        </header>

        {trocas.length === 0 ? (
          <p className="historico__vazio">Nada ainda. Fale ou digite algo para o Jarvis.</p>
        ) : (
          <ol className="historico__lista">
            {trocas.map((troca) => (
              <li key={troca.id} className="historico__troca">
                <span className="historico__hora">{formatarHora(troca.quando)}</span>
                <p className="historico__pergunta">{troca.pergunta}</p>
                <p className="historico__resposta">
                  <span className="comando__quem">J.A.R.V.I.S. ›</span> {troca.resposta}
                </p>
              </li>
            ))}
          </ol>
        )}
      </aside>
    </div>
  );
}
