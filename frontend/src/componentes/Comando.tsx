import type { RefObject } from "react";
import type { Habilidade } from "../api";
import { type EstadoGravacao, estadoDoNucleo } from "../gravacao";
import { cumprimento, formatarData, formatarHoraCompleta } from "../tempo";
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
        <h2 className="comando__titulo">Sistema</h2>
        <Leitura rotulo="Backend" valor="ONLINE" ok />
        <Leitura rotulo="Operador" valor={usuario.toUpperCase()} />
        <Leitura rotulo="Rostos" valor={String(cadastrados.length).padStart(2, "0")} />
        <Leitura rotulo="Microfone" valor={gravando ? "OUVINDO" : "LIVRE"} ok={gravando || undefined} />
        <Leitura rotulo="Versão" valor={versao} />

        <div className="comando__acoes">
          <button className="comando__acao" type="button" onClick={onCadastrarRosto}>
            <span aria-hidden="true">＋</span> Rosto
          </button>
          <button className="comando__acao" type="button" onClick={onConfigurarPin}>
            <span aria-hidden="true">＋</span> PIN
          </button>
        </div>
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
        <p className="comando__relogio">{formatarHoraCompleta(agora)}</p>
        <p className="comando__data">{formatarData(agora)}</p>

        <h2 className="comando__titulo">Habilidades</h2>
        <ul className="comando__habilidades">
          {habilidades.map((habilidade) => (
            <li key={habilidade.id} className={`habilidade habilidade--${habilidade.situacao}`}>
              <span className="habilidade__marca" aria-hidden="true" />
              <span className="habilidade__nome">{habilidade.nome}</span>
              <span className="habilidade__situacao">
                {habilidade.situacao === "pronta" ? "ATIVA" : "EM BREVE"}
              </span>
            </li>
          ))}
        </ul>
      </aside>

      <footer className="comando__conversa">
        <span className="comando__rotulo">Voz</span>
        <OndaVoz nivel={nivel} cor={CORES[nucleo.tom]} />
        <kbd className={`comando__tecla ${gravando ? "comando__tecla--apertada" : ""}`}>ESPAÇO</kbd>
      </footer>
    </main>
  );
}

function Leitura({ rotulo, valor, ok }: { rotulo: string; valor: string; ok?: boolean }) {
  return (
    <p className="comando__leitura">
      <span className="comando__leitura-rotulo">{rotulo}</span>
      <span className={`comando__leitura-valor ${ok ? "comando__leitura-valor--ok" : ""}`}>
        {valor}
      </span>
    </p>
  );
}
