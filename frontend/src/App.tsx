import { useCallback, useEffect, useRef, useState } from "react";
import { bloquearSessao } from "./api";
import { BarraTopo } from "./componentes/BarraTopo";
import { PainelHabilidades } from "./componentes/PainelHabilidades";
import { PainelSistema } from "./componentes/PainelSistema";
import { PainelVoz } from "./componentes/PainelVoz";
import { Saudacao } from "./componentes/Saudacao";
import { TelaBloqueio } from "./componentes/TelaBloqueio";
import { useConexaoBackend } from "./hooks/useConexaoBackend";
import { useGravacao } from "./hooks/useGravacao";
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

  // Bloquear é decisão do backend. Só voltamos para a tela de bloqueio depois que
  // ele confirma: se trancássemos só aqui, a tela reabriria no primeiro quadro,
  // porque a sessão de lá continuaria aberta e responderia "desbloqueado".
  const [bloqueio, setBloqueio] = useState<{ emAndamento: boolean; erro: string | null }>({
    emAndamento: false,
    erro: null,
  });

  const aoBloquear = useCallback(async () => {
    setBloqueio({ emAndamento: true, erro: null });
    try {
      await bloquearSessao();
      setUsuario(null);
      setBloqueio({ emAndamento: false, erro: null });
    } catch (erro) {
      setBloqueio({
        emAndamento: false,
        erro: erro instanceof Error ? erro.message : String(erro),
      });
    }
  }, []);

  // Segurar ESPAÇO grava a voz. Só depois de desbloquear: na tela de bloqueio o
  // espaço não deve fazer nada.
  const gravacao = useGravacao(!!usuario && conexao.estado === "conectado");

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
      <BarraTopo
        conexao={conexao}
        nomeAssistente={nomeAssistente}
        onBloquear={aoBloquear}
        bloqueando={bloqueio.emAndamento}
      />
      <main className="conteudo">
        <Saudacao agora={agora} nome={usuario} />

        {bloqueio.erro && (
          <div className="aviso" role="alert">
            <strong>Não consegui bloquear.</strong> {bloqueio.erro}
          </div>
        )}

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
            <PainelVoz gravacao={gravacao} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
