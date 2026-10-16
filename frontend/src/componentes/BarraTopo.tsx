import type { Conexao } from "../hooks/useConexaoBackend";

type Props = {
  conexao: Conexao;
  nomeAssistente: string;
};

export function BarraTopo({ conexao, nomeAssistente }: Props) {
  return (
    <header className="barra-topo">
      <div className="barra-topo__marca">
        <span className={`reator reator--${conexao.estado}`} aria-hidden="true" />
        {nomeAssistente}
      </div>
      <div className="barra-topo__acoes">
        <IndicadorConexao conexao={conexao} />
        {/* Passa a funcionar no Passo 5 da Fase 2 */}
        <button className="botao" type="button" disabled title="Em breve">
          🔒 Bloquear
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
