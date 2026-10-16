import { useEffect, useState } from "react";
import { buscarStatus, type Status } from "./api";
import "./App.css";

// De quanto em quanto tempo o app confere se o backend está vivo.
const INTERVALO_VERIFICACAO_MS = 3000;

type Conexao =
  | { estado: "verificando" }
  | { estado: "conectado"; status: Status }
  | { estado: "desconectado" };

function useConexaoBackend(): Conexao {
  const [conexao, setConexao] = useState<Conexao>({ estado: "verificando" });

  useEffect(() => {
    let ativo = true;

    async function verificar() {
      try {
        const status = await buscarStatus();
        if (ativo) setConexao({ estado: "conectado", status });
      } catch {
        if (ativo) setConexao({ estado: "desconectado" });
      }
    }

    verificar();
    const intervalo = setInterval(verificar, INTERVALO_VERIFICACAO_MS);
    return () => {
      ativo = false;
      clearInterval(intervalo);
    };
  }, []);

  return conexao;
}

function App() {
  const conexao = useConexaoBackend();

  return (
    <main className="tela">
      <div className={`nucleo nucleo--${conexao.estado}`} aria-hidden="true" />
      <h1 className="marca">J.A.R.V.I.S.</h1>
      <IndicadorConexao conexao={conexao} />
      {conexao.estado === "conectado" && (
        <ListaHabilidades habilidades={conexao.status.habilidades} />
      )}
    </main>
  );
}

function IndicadorConexao({ conexao }: { conexao: Conexao }) {
  if (conexao.estado === "verificando") {
    return <p className="subtitulo">Conectando...</p>;
  }
  if (conexao.estado === "desconectado") {
    return (
      <div className="aviso">
        <p className="subtitulo subtitulo--erro">🔴 Backend desconectado</p>
        <p className="dica">
          Rode no terminal: <code>cd backend && uv run python -m jarvis servidor</code>
        </p>
      </div>
    );
  }
  return (
    <p className="subtitulo subtitulo--ok">🟢 Conectado · v{conexao.status.versao}</p>
  );
}

function ListaHabilidades({ habilidades }: { habilidades: Status["habilidades"] }) {
  return (
    <section className="painel">
      <h2 className="painel__titulo">Habilidades</h2>
      <ul className="habilidades">
        {habilidades.map((habilidade) => (
          <li key={habilidade.id} className="habilidade">
            <span className="habilidade__icone" aria-hidden="true">
              ✓
            </span>
            <div>
              <strong>{habilidade.nome}</strong>
              <p>{habilidade.descricao}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

export default App;
