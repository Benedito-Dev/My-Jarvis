import {
  type FormEvent,
  type RefObject,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { Habilidade, Lembrete } from "../api";
import {
  duracaoDaFala,
  type EstadoGravacao,
  estadoDoNucleo,
  registrarTroca,
  type Troca,
} from "../gravacao";
import { MS_POR_LETRA, useDigitando } from "../hooks/useDigitando";
import { cumprimento } from "../tempo";
import { ModuloHabilidades, ModuloLembretes, ModuloSistema, ModuloTempo } from "./ModulosComando";
import { useVozDoJarvis } from "../hooks/useVozDoJarvis";
import { HistoricoConversa } from "./HistoricoConversa";
import { type ModoNucleo, Nucleo } from "./Nucleo";
import { OndaVoz } from "./OndaVoz";
import "./comando.css";

// A central de comando: o painel depois do desbloqueio. O núcleo no centro é o
// Jarvis; as colunas dos lados mostram só dados reais, cada um com seu rótulo.

// Acima disto (pergunta + resposta), o núcleo encolhe para o texto caber.
const LETRAS_PARA_ENCOLHER = 140;

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
  lembretes: Lembrete[];
  gravacao: EstadoGravacao;
  nivel: RefObject<number>;
  onEnviarTexto: (texto: string) => void;
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
  lembretes,
  gravacao,
  nivel,
  onEnviarTexto,
  onCadastrarRosto,
  onConfigurarPin,
}: Props) {
  const nucleo = estadoDoNucleo(gravacao);

  // Histórico da conversa desta sessão: cada troca entra quando termina.
  const [historico, setHistorico] = useState<Troca[]>([]);
  const [historicoAberto, setHistoricoAberto] = useState(false);
  const fecharHistorico = useCallback(() => setHistoricoAberto(false), []);
  // A mesma conversa só entra uma vez (o React pode rodar este efeito em dobro).
  const ultimaRegistrada = useRef<EstadoGravacao | null>(null);
  useEffect(() => {
    if (ultimaRegistrada.current === gravacao) return;
    ultimaRegistrada.current = gravacao;
    setHistorico((atual) => registrarTroca(atual, gravacao, new Date()));
  }, [gravacao]);

  // Para quando não dá para falar: digita e aperta Enter.
  const [digitado, setDigitado] = useState("");
  function enviarDigitado(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!digitado.trim()) return;
    onEnviarTexto(digitado);
    setDigitado("");
  }
  // O detalhe aparece digitando: no "Você disse", é a sua frase sendo escrita.
  const detalhe = useDigitando(nucleo.detalhe);
  const falaOuvida = gravacao.estado === "ouvida" && gravacao.texto !== "";
  const gravando = gravacao.estado === "gravando";

  // A resposta do Jarvis entra digitando logo depois que a sua frase termina.
  const resposta = gravacao.estado === "ouvida" ? gravacao.resposta : null;
  const respostaVisivel = useDigitando(resposta ?? "", nucleo.detalhe.length * MS_POR_LETRA + 250);

  // Resposta longa (comum com a IA): o núcleo encolhe para abrir espaço ao texto.
  const conversaLonga = (resposta?.length ?? 0) + nucleo.detalhe.length > LETRAS_PARA_ENCOLHER;

  // Enquanto ele fala a resposta, o núcleo "fala" junto. A resposta chega frase a
  // frase; cada frase nova empurra o fim da fala para mais adiante.
  const [falandoAte, setFalandoAte] = useState(0);
  const respostaAnterior = useRef("");
  useEffect(() => {
    const atual = resposta ?? "";
    const anterior = respostaAnterior.current;
    respostaAnterior.current = atual;
    const nova = atual.startsWith(anterior) ? atual.slice(anterior.length).trim() : atual;
    if (!nova) return;
    setFalandoAte((ate) => Math.max(ate, Date.now()) + duracaoDaFala(nova));
  }, [resposta]);
  const [falando, setFalando] = useState(false);
  useEffect(() => {
    const falta = falandoAte - Date.now();
    if (falta <= 0) return;
    setFalando(true);
    const temporizador = setTimeout(() => setFalando(false), falta);
    return () => clearTimeout(temporizador);
  }, [falandoAte]);

  // A voz de verdade (envelope vindo do backend). Sem ela, fica a estimativa acima.
  const voz = useVozDoJarvis();

  const esperandoResposta =
    gravacao.estado === "enviando" ||
    (gravacao.estado === "ouvida" && !gravacao.resposta && !gravacao.terminou);
  const modo: ModoNucleo = gravando
    ? "ouvindo"
    : esperandoResposta
      ? "pensando"
      : voz.temEnvelope
        ? voz.falando
          ? "voz"
          : "calmo"
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
        <ModuloLembretes lembretes={lembretes} agora={agora} />
      </aside>

      <section className={`comando__centro ${conversaLonga ? "comando__centro--longa" : ""}`}>
        <div className="comando__nucleo">
          <Nucleo niveis={[nivel, voz.nivel]} tom={nucleo.tom} modo={modo} />
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
        <form className="comando__digitar" onSubmit={enviarDigitado}>
          <span className="comando__rotulo" aria-hidden="true">
            ›
          </span>
          <input
            className="comando__entrada"
            value={digitado}
            onChange={(evento) => setDigitado(evento.target.value)}
            placeholder="Digite para o Jarvis… ou segure ESPAÇO para falar"
            maxLength={500}
            aria-label="Mensagem para o Jarvis"
          />
        </form>
        <OndaVoz niveis={[nivel, voz.nivel]} cor={CORES[nucleo.tom]} />
        <kbd className={`comando__tecla ${gravando ? "comando__tecla--apertada" : ""}`}>ESPAÇO</kbd>
        <button
          className="comando__historico"
          type="button"
          onClick={() => setHistoricoAberto(true)}
          title="Histórico da conversa"
        >
          Histórico <span className="comando__contador">{historico.length}</span>
        </button>
      </footer>

      {historicoAberto && (
        <HistoricoConversa trocas={historico} onFechar={fecharHistorico} />
      )}
    </main>
  );
}
