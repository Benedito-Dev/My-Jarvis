import type { Conexao } from "../hooks/useConexaoBackend";

type Props = {
  conexao: Conexao;
  nomeAssistente: string;
  onBloquear: () => void;
  bloqueando: boolean;
};

export function BarraTopo({ conexao, nomeAssistente, onBloquear, bloqueando }: Props) {
  // Sem backend não há como bloquear: quem guarda o estado da sessão é ele.
  const indisponivel = conexao.estado !== "conectado";
  return (
    <header className="barra-topo">
      <div className="barra-topo__marca">
        <span className={`reator reator--${conexao.estado}`} aria-hidden="true" />
        {nomeAssistente}
      </div>
      <div className="barra-topo__acoes">
        <IndicadorConexao conexao={conexao} />
        <button
          className="botao"
          type="button"
          onClick={onBloquear}
          disabled={bloqueando || indisponivel}
          title={indisponivel ? "Backend desconectado" : "Voltar para a tela de bloqueio"}
        >
          🔒 {bloqueando ? "Bloqueando..." : "Bloquear"}
        </button>
      </div>
    </header>
  );
}

function IndicadorConexao({ conexao }: { conexao: Conexao }) {
  const textos = {
    verificando: "Conectando...",
    conectado: "Online",
    desconectado: "Offline",
  };
  return (
    <span className={`indicador indicador--${conexao.estado}`}>
      <span className="indicador__ponto" aria-hidden="true" />
      {textos[conexao.estado]}
    </span>
  );
}
