import { useEffect, useState } from "react";
import {
  buscarRostos,
  buscarSessao,
  buscarStatus,
  type Rostos,
  type Sessao,
  type Status,
} from "../api";
import { guardarLatencia } from "../modulos";

// De quanto em quanto tempo o app confere se o backend está vivo.
const INTERVALO_VERIFICACAO_MS = 3000;

export type Conexao =
  | { estado: "verificando" }
  | {
      estado: "conectado";
      status: Status;
      rostos: Rostos;
      sessao: Sessao;
      /** Quanto o backend levou para responder, em ms, das mais antigas às mais novas. */
      latencias: number[];
    }
  | { estado: "desconectado" };

export function useConexaoBackend(): Conexao {
  const [conexao, setConexao] = useState<Conexao>({ estado: "verificando" });

  useEffect(() => {
    let ativo = true;
    let latencias: number[] = [];

    async function verificar() {
      try {
        const inicio = performance.now();
        const [status, sessao] = await Promise.all([
          buscarStatus(),
          buscarSessao(),
        ]);
        latencias = guardarLatencia(latencias, performance.now() - inicio);
        // Nomes de rostos são dados de sessão: não entram no cliente enquanto
        // o Jarvis estiver bloqueado. Isso evita enumeração antes do login.
        const rostos = sessao.usuario
          ? await buscarRostos()
          : { cadastrados: [] };
        if (ativo) setConexao({ estado: "conectado", status, rostos, sessao, latencias });
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
