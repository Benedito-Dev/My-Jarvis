import { useCallback, useEffect, useRef, useState } from "react";
import { BarraTopo } from "./componentes/BarraTopo";
import { PainelHabilidades } from "./componentes/PainelHabilidades";
import { PainelSistema } from "./componentes/PainelSistema";
import { Saudacao } from "./componentes/Saudacao";
import { TelaBloqueio } from "./componentes/TelaBloqueio";
import { useConexaoBackend } from "./hooks/useConexaoBackend";
import { useRelogio } from "./hooks/useRelogio";
import "./App.css";

// Usado só enquanto o backend não responde; o nome de verdade vem de /status.
const NOME_RESERVA = "J.A.R.V.I.S.";

function App() {
  const conexao = useConexaoBackend();
  const agora = useRelogio();

  const nomeAssistente =
    conexao.estado === "conectado" ? conexao.status.nome : NOME_RESERVA;

  useEffect(() => {
    document.title = nomeAssistente;
  }, [nomeAssistente]);

  // Quem desbloqueou. Vem da tela de bloqueio (depois do "Bem-vindo") ou, se o app
  // abrir com a sessão do backend já desbloqueada, da primeira resposta do backend.
  const [usuario, setUsuario] = useState<string | null>(null);
  const aoDesbloquear = useCallback((nome: string) => setUsuario(nome), []);
  const sessaoInicialLida = useRef(false);

  useEffect(() => {
    if (conexao.estado !== "conectado" || sessaoInicialLida.current) return;
    sessaoInicialLida.current = true;
    if (conexao.sessao.usuario) setUsuario(conexao.sessao.usuario);
  }, [conexao]);

  if (!usuario) {
    return (
      <TelaBloqueio
        nomeAssistente={nomeAssistente}
        backendOnline={conexao.estado === "conectado"}
        onDesbloqueado={aoDesbloquear}
      />
    );
  }

  return (
    <div className="app">
      <BarraTopo conexao={conexao} nomeAssistente={nomeAssistente} />
      <main className="conteudo">
        <Saudacao agora={agora} nome={usuario} />

        {conexao.estado === "desconectado" && (
          <div className="aviso" role="alert">
            <strong>Backend desconectado.</strong> Rode no terminal:{" "}
            <code>cd backend && uv run python -m jarvis servidor</code>
          </div>
        )}

        {conexao.estado === "conectado" && (
          <div className="paineis">
            <PainelHabilidades habilidades={conexao.status.habilidades} />
            <PainelSistema
              versao={conexao.status.versao}
              cadastrados={conexao.rostos.cadastrados}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
