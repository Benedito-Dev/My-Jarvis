import { useEffect, useState } from "react";
import {
  buscarLembretes,
  buscarRostos,
  buscarSessao,
  buscarStatus,
  type Lembrete,
  type Rostos,
  type Sessao,
  type Status,
} from "../api";
import { guardarLatencia } from "../modulos";

// De quanto em quanto tempo o app confere se o backend está vivo.
const INTERVALO_VERIFICACAO_MS = 3000;
// O app liga o backend ao abrir (src-tauri/src/backend.rs), e ele leva alguns
// segundos carregando os modelos. Até lá, "verificando" (iniciando), não "desconectado".
const TEMPO_PARA_LIGAR_MS = 60_000;

export type Conexao =
  | { estado: "verificando" }
  | {
      estado: "conectado";
      status: Status;
      rostos: Rostos;
      sessao: Sessao;
      /** Quanto o backend levou para responder, em ms, das mais antigas às mais novas. */
      latencias: number[];
      /** Quando (Date.now) foi feita a pergunta que trouxe esta resposta. */
      perguntadoEm: number;
      /** Lembretes que ainda vão tocar (vazio com o Jarvis bloqueado). */
      lembretes: Lembrete[];
    }
  | { estado: "desconectado" };

export function useConexaoBackend(): Conexao {
  const [conexao, setConexao] = useState<Conexao>({ estado: "verificando" });

  useEffect(() => {
    let ativo = true;
    let latencias: number[] = [];
    let jaConectou = false;
    const abriuEm = Date.now();

    async function verificar() {
      try {
        const perguntadoEm = Date.now();
        const inicio = performance.now();
        const [status, sessao] = await Promise.all([
          buscarStatus(),
          buscarSessao(),
        ]);
        latencias = guardarLatencia(latencias, performance.now() - inicio);
        // Nomes de rostos são dados de sessão: não entram no cliente enquanto
        // o Jarvis estiver bloqueado. Isso evita enumeração antes do login.
        const [rostos, lembretes] = sessao.usuario
          ? await Promise.all([buscarRostos(), buscarLembretes()])
          : [{ cadastrados: [] }, []];
        jaConectou = true;
        if (ativo) {
          setConexao({
            estado: "conectado",
            status,
            rostos,
            sessao,
            latencias,
            perguntadoEm,
            lembretes,
          });
        }
      } catch {
        const aindaLigando = !jaConectou && Date.now() - abriuEm < TEMPO_PARA_LIGAR_MS;
        if (ativo) setConexao({ estado: aindaLigando ? "verificando" : "desconectado" });
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
