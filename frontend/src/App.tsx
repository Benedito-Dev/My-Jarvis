import { useCallback, useEffect, useRef, useState } from "react";
import { bloquearSessao } from "./api";
import { BarraTopo } from "./componentes/BarraTopo";
import { Comando } from "./componentes/Comando";
import { TelaBloqueio } from "./componentes/TelaBloqueio";
import { TelaCadastro } from "./componentes/TelaCadastro";
import { TelaCadastroPin } from "./componentes/TelaCadastroPin";
import { useConexaoBackend } from "./hooks/useConexaoBackend";
import { useGravacao } from "./hooks/useGravacao";
import { useRelogio } from "./hooks/useRelogio";
import "./App.css";

// Usado só enquanto o backend não responde; o nome de verdade vem de /status.
const NOME_RESERVA = "J.A.R.V.I.S.";

// Quanto tempo a tela de bloqueio fica por baixo enquanto o painel se abre por cima.
// Igual à animação `revelar-painel` do App.css.
const DURACAO_REVELACAO_MS = 900;

function App() {
  const conexao = useConexaoBackend();
  const agora = useRelogio();

  const nomeAssistente = conexao.estado === "conectado" ? conexao.status.nome : NOME_RESERVA;

  useEffect(() => {
    document.title = nomeAssistente;
  }, [nomeAssistente]);

  // Quem desbloqueou. Vem da tela de bloqueio (depois do "Bem-vindo") ou, se o app
  // abrir com a sessão do backend já desbloqueada, da primeira resposta do backend.
  const [usuario, setUsuario] = useState<string | null>(null);
  // Quando o app desbloqueou (Date.now): respostas perguntadas antes disso são velhas.
  const desbloqueouEm = useRef(0);
  const aoDesbloquear = useCallback((nome: string) => {
    desbloqueouEm.current = Date.now();
    setUsuario(nome);
  }, []);

  // Desde quando a sessão está aberta: o painel mostra o tempo de sessão.
  const [desbloqueadoEm, setDesbloqueadoEm] = useState(() => new Date());
  useEffect(() => {
    if (usuario) setDesbloqueadoEm(new Date());
  }, [usuario]);
  const sessaoInicialLida = useRef(false);

  useEffect(() => {
    if (conexao.estado !== "conectado" || sessaoInicialLida.current) return;
    sessaoInicialLida.current = true;
    if (conexao.sessao.usuario) {
      desbloqueouEm.current = Date.now();
      setUsuario(conexao.sessao.usuario);
      setBloqueioMontado(false); // já abriu desbloqueado: não há transição a mostrar
    }
  }, [conexao]);

  // Quem manda na sessão é o backend. Se ele diz que está bloqueado (reiniciou,
  // ou alguém bloqueou por outro caminho), o painel fecha. Só vale resposta
  // perguntada depois do desbloqueio: uma mais velha ainda diria "bloqueado".
  useEffect(() => {
    if (!usuario || conexao.estado !== "conectado") return;
    if (conexao.sessao.usuario === null && conexao.perguntadoEm > desbloqueouEm.current) {
      setUsuario(null);
    }
  }, [conexao, usuario]);

  // A tela de bloqueio sai devagar: depois de desbloquear ela continua montada
  // por baixo, enquanto o painel se abre a partir do visor.
  const [bloqueioMontado, setBloqueioMontado] = useState(true);
  useEffect(() => {
    if (!usuario) {
      setBloqueioMontado(true);
      return;
    }
    const temporizador = setTimeout(() => setBloqueioMontado(false), DURACAO_REVELACAO_MS);
    return () => clearTimeout(temporizador);
  }, [usuario]);

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
  const { gravacao, nivel } = useGravacao(!!usuario && conexao.estado === "conectado");

  // Cadastrar rosto pelo app, sem terminal. Cada máquina precisa do seu
  // próprio cadastro, porque dados/ não vai para o git (decisão 0012).
  const [cadastrando, setCadastrando] = useState(false);
  const [configurandoPin, setConfigurandoPin] = useState(false);

  // A tela de bloqueio fica sempre na mesma posição da árvore: se mudasse de
  // lugar, o React a recriaria no meio da transição (câmera e abertura de novo).
  return (
    <>
      {usuario && (
        <div className="app app--revelando">
          <BarraTopo
            conexao={conexao}
            nomeAssistente={nomeAssistente}
            onBloquear={aoBloquear}
            bloqueando={bloqueio.emAndamento}
          />
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
            <Comando
              usuario={usuario}
              agora={agora}
              desbloqueadoEm={desbloqueadoEm}
              latencias={conexao.latencias}
              versao={conexao.status.versao}
              cadastrados={conexao.rostos.cadastrados}
              habilidades={conexao.status.habilidades}
              gravacao={gravacao}
              nivel={nivel}
              onCadastrarRosto={() => setCadastrando(true)}
              onConfigurarPin={() => setConfigurandoPin(true)}
            />
          )}

          {cadastrando && (
            <TelaCadastro
              onFechar={() => setCadastrando(false)}
              onCadastrado={() => {
                // A lista de rostos vem do backend; o useConexaoBackend recarrega
                // sozinho a cada 3s, então não precisamos mexer nela aqui.
              }}
            />
          )}

          {configurandoPin && usuario && (
            <TelaCadastroPin
              usuario={usuario}
              onFechar={() => setConfigurandoPin(false)}
              onConfigurado={() => setConfigurandoPin(false)}
            />
          )}
        </div>
      )}

      {/* A borda de luz do círculo que abre o painel (só durante a transição). */}
      {usuario && bloqueioMontado && <div className="revelacao__anel" aria-hidden="true" />}

      {(!usuario || bloqueioMontado) && (
        <TelaBloqueio
          nomeAssistente={nomeAssistente}
          backendOnline={conexao.estado === "conectado"}
          onDesbloqueado={aoDesbloquear}
          saindo={!!usuario}
        />
      )}
    </>
  );
}

export default App;
