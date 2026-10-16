import { useEffect, useState } from "react";
import {
  buscarRostos,
  buscarSessao,
  buscarStatus,
  type Rostos,
  type Sessao,
  type Status,
} from "../api";

// De quanto em quanto tempo o app confere se o backend está vivo.
const INTERVALO_VERIFICACAO_MS = 3000;

export type Conexao =
  | { estado: "verificando" }
  | { estado: "conectado"; status: Status; rostos: Rostos; sessao: Sessao }
  | { estado: "desconectado" };

export function useConexaoBackend(): Conexao {
  const [conexao, setConexao] = useState<Conexao>({ estado: "verificando" });

  useEffect(() => {
    let ativo = true;

    async function verificar() {
      try {
        const [status, rostos, sessao] = await Promise.all([
          buscarStatus(),
          buscarRostos(),
          buscarSessao(),
        ]);
        if (ativo) setConexao({ estado: "conectado", status, rostos, sessao });
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
