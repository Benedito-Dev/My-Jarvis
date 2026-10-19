import { type RefObject, useEffect, useState } from "react";
import type { Habilidade } from "../api";
import { duracaoDaFala, type EstadoGravacao, estadoDoNucleo } from "../gravacao";
import { MS_POR_LETRA, useDigitando } from "../hooks/useDigitando";
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
  // O detalhe aparece digitando: no "Você disse", é a sua frase sendo escrita.
  const detalhe = useDigitando(nucleo.detalhe);
  const falaOuvida = gravacao.estado === "ouvida" && gravacao.texto !== "";
  const gravando = gravacao.estado === "gravando";

  // A resposta do Jarvis entra digitando logo depois que a sua frase termina.
  const resposta = gravacao.estado === "ouvida" ? gravacao.resposta : null;
  const respostaVisivel = useDigitando(resposta ?? "", nucleo.detalhe.length * MS_POR_LETRA + 250);

  // Enquanto ele fala a resposta, o núcleo "fala" junto.
  const [falando, setFalando] = useState(false);
  useEffect(() => {
    if (gravacao.estado !== "ouvida" || !gravacao.resposta) return;
    setFalando(true);
    const temporizador = setTimeout(() => setFalando(false), duracaoDaFala(gravacao.resposta));
    return () => {
      clearTimeout(temporizador);
      setFalando(false);
    };
  }, [gravacao]);

  const modo: ModoNucleo = gravando
    ? "ouvindo"
    : gravacao.estado === "enviando"
      ? "pensando"
      : falando
        ? "falando"
        : "calmo";

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
        <p className={`comando__detalhe ${falaOuvida ? "comando__detalhe--fala" : ""}`}>
          {detalhe}
          {!resposta && <span className="comando__cursor" aria-hidden="true" />}
        </p>
        {resposta && (
          <p className="comando__resposta">
            <span className="comando__quem">{"J.A.R.V.I.S. ›"}</span> {respostaVisivel}
            <span className="comando__cursor" aria-hidden="true" />
          </p>
        )}
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
