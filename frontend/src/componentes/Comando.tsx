import type { RefObject } from "react";
import type { Habilidade } from "../api";
import { type EstadoGravacao, estadoDoNucleo } from "../gravacao";
import { cumprimento } from "../tempo";
import { ModuloHabilidades, ModuloSistema, ModuloTempo } from "./ModulosComando";
import { type ModoNucleo, Nucleo } from "./Nucleo";
import { OndaVoz } from "./OndaVoz";
import "./comando.css";

// A central de comando: o painel depois do desbloqueio. O núcleo no centro é o
// Jarvis; as colunas dos lados mostram só dados reais, cada um com seu rótulo.

const CORES = {
  aviso: "57, 197, 255",
  ok: "61, 220, 132",
  erro: "255, 90, 95",
  pensando: "169, 112, 255",
};

type Props = {
  usuario: string;
  agora: Date;
  desbloqueadoEm: Date;
  latencias: number[];
  versao: string;
  cadastrados: string[];
  habilidades: Habilidade[];
  gravacao: EstadoGravacao;
  nivel: RefObject<number>;
  onCadastrarRosto: () => void;
  onConfigurarPin: () => void;
};

export function Comando({
  usuario,
  agora,
  desbloqueadoEm,
  latencias,
  versao,
  cadastrados,
  habilidades,
  gravacao,
  nivel,
  onCadastrarRosto,
  onConfigurarPin,
}: Props) {
  const nucleo = estadoDoNucleo(gravacao);
  const gravando = gravacao.estado === "gravando";
  const modo: ModoNucleo = gravando ? "ouvindo" : gravacao.estado === "enviando" ? "pensando" : "calmo";

  return (
    <main className={`comando comando--${nucleo.tom}`}>
      <aside className="comando__coluna comando__coluna--esquerda">
        <ModuloSistema
          usuario={usuario}
          agora={agora}
          desbloqueadoEm={desbloqueadoEm}
          latencias={latencias}
          rostos={cadastrados.length}
          ouvindo={gravando}
          versao={versao}
          onCadastrarRosto={onCadastrarRosto}
          onConfigurarPin={onConfigurarPin}
        />
      </aside>

      <section className="comando__centro">
        <div className="comando__nucleo">
          <Nucleo nivel={nivel} tom={nucleo.tom} modo={modo} />
        </div>
        <p className="comando__cumprimento">
          {cumprimento(agora)}, <strong>{usuario}</strong>.
        </p>
        <p className="comando__estado" role="status">
          {nucleo.titulo}
        </p>
        <p className="comando__detalhe">{nucleo.detalhe}</p>
      </section>

      <aside className="comando__coluna comando__coluna--direita">
        <ModuloTempo agora={agora} />
        <ModuloHabilidades habilidades={habilidades} />
      </aside>

      <footer className="comando__conversa">
        <span className="comando__rotulo">Voz</span>
        <OndaVoz nivel={nivel} cor={CORES[nucleo.tom]} />
        <kbd className={`comando__tecla ${gravando ? "comando__tecla--apertada" : ""}`}>ESPAÇO</kbd>
      </footer>
    </main>
  );
}
