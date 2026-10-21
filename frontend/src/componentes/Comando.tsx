import {
  type FormEvent,
  type RefObject,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";
import type { Habilidade, Lembrete } from "../api";
import { type Cartao, arrumarCartoes, cartoesJaFalados } from "../cartoes";
import {
  duracaoDaFala,
  type EstadoGravacao,
  estadoDoNucleo,
  type FasePainel,
  faseDoPainel,
  registrarTroca,
  type Troca,
} from "../gravacao";
import { MS_POR_LETRA, useDigitando } from "../hooks/useDigitando";
import { type Escuta, useEscuta } from "../hooks/useEscuta";
import { useSustentado } from "../hooks/useSustentado";
import { duracaoDesde, resumoDosLembretes } from "../modulos";
import { cumprimento, formatarData, formatarHora } from "../tempo";
import {
  Canto,
  ModuloHabilidades,
  ModuloLembretes,
  ModuloSistema,
  ModuloTempo,
} from "./ModulosComando";
import { useVozDoJarvis } from "../hooks/useVozDoJarvis";
import { CartaoDestaque, CartaoMini, CartaoProgresso } from "./Cartoes";
import { HistoricoConversa } from "./HistoricoConversa";
import { type ModoNucleo, Nucleo } from "./Nucleo";
import { OndaVoz } from "./OndaVoz";
import "./comando.css";

// A central de comando: o painel depois do desbloqueio. A tela é a conversa:
// no centro, o orbe (o Jarvis), a manchete do que ele está fazendo e a legenda
// do que ele fala. Os dados ficam em resumos pequenos nos cantos; um clique
// abre o módulo inteiro.

// Pausa máxima entre duas frases que ainda conta como a mesma fala.
const FOLGA_DA_FALA_MS = 1500;
// Quanto esperar a voz começar depois que a resposta chegou, antes de desistir dela.
const ESPERA_MAXIMA_DA_VOZ_MS = 5000;
type NomeCanto = "sistema" | "lembretes" | "tempo" | "habilidades";

const MANCHETES: Record<FasePainel, string> = {
  espera: "Em espera",
  ouvindo: "Ouvindo",
  pensando: "Pensando",
  falando: "Falando",
};

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
  onEnviarPedido: (audio: Blob, chamado: boolean) => void;
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
  onEnviarPedido,
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

  // Entre duas frases a voz para um instante: a folga segura o "falando", para
  // a manchete e o cartão não piscarem a cada pausa.
  const falandoAgora = modo === "voz" || modo === "falando";
  const falandoComFolga = useSustentado(falandoAgora, FOLGA_DA_FALA_MS);
  // A resposta pode chegar inteira antes de a voz começar (a voz leva um tempo
  // para ser gerada). Até ela começar, a conversa não acabou. Se a voz não vier
  // (sem som, erro), desiste depois de um tempo.
  const [falouNestaConversa, setFalouNestaConversa] = useState(false);
  useEffect(() => {
    if (gravacao.estado !== "ouvida") setFalouNestaConversa(false);
  }, [gravacao.estado]);
  useEffect(() => {
    if (falandoAgora) setFalouNestaConversa(true);
  }, [falandoAgora]);
  const aguardandoVoz =
    gravacao.estado === "ouvida" && gravacao.resposta !== "" && !falouNestaConversa;
  useEffect(() => {
    if (!aguardandoVoz) return;
    const temporizador = setTimeout(() => setFalouNestaConversa(true), ESPERA_MAXIMA_DA_VOZ_MS);
    return () => clearTimeout(temporizador);
  }, [aguardandoVoz]);
  const faseDaConversa = faseDoPainel(gravacao, falandoComFolga, aguardandoVoz);
  // Sem tecla: "Jarvis" acorda. Ocupado (falando, pensando, gravando), ele não
  // procura o nome, para não acordar com a própria voz.
  const escuta = useEscuta(true, faseDaConversa !== "espera" || gravando, onEnviarPedido);
  // Depois do "Pois não?", ele está ouvindo o pedido: a tela mostra.
  const ouvindoPedido = escuta.atencao === "pedido";
  const fase: FasePainel = ouvindoPedido ? "ouvindo" : faseDaConversa;
  const pediuParaEscutar = useRef<EstadoGravacao | null>(null);
  useEffect(() => {
    if (gravacao.estado !== "ouvida" || gravacao.acao !== "escutar" || !gravacao.terminou) return;
    if (faseDaConversa !== "espera" || pediuParaEscutar.current === gravacao) return;
    pediuParaEscutar.current = gravacao;
    escuta.escutarAgora();
  }, [gravacao, faseDaConversa, escuta]);
  // Erro ou "não entendi" aparecem na própria manchete, para não passarem despercebidos.
  const deuErrado =
    gravacao.estado === "erro" || (gravacao.estado === "ouvida" && gravacao.texto === "");
  const manchete = deuErrado ? nucleo.titulo : MANCHETES[fase];
  const sublinha = deuErrado
    ? nucleo.detalhe
    : fase === "espera"
      ? `${cumprimento(agora)}, ${usuario}`
      : fase === "ouvindo"
        ? ouvindoPedido
          ? "Pode falar"
          : "Solte ESPAÇO quando terminar"
        : fase === "pensando"
          ? "Preparando a resposta"
          : "";

  // Um canto aberto por vez. ESC ou um clique fora fecham.
  const [cantoAberto, setCantoAberto] = useState<NomeCanto | null>(null);
  const alternar = (nome: NomeCanto) => () =>
    setCantoAberto((atual) => (atual === nome ? null : nome));
  useEffect(() => {
    if (!cantoAberto) return;
    const fecharComEsc = (evento: KeyboardEvent) => {
      if (evento.key === "Escape") setCantoAberto(null);
    };
    const fecharClicandoFora = (evento: PointerEvent) => {
      if (!(evento.target as Element).closest(".canto")) setCantoAberto(null);
    };
    window.addEventListener("keydown", fecharComEsc);
    window.addEventListener("pointerdown", fecharClicandoFora);
    return () => {
      window.removeEventListener("keydown", fecharComEsc);
      window.removeEventListener("pointerdown", fecharClicandoFora);
    };
  }, [cantoAberto]);

  // Cartões: os desta conversa ficam em destaque enquanto ele trabalha e fala;
  // quando outra conversa começa, eles passam para a sessão (a fileira de baixo).
  const [anteriores, setAnteriores] = useState<Cartao[]>([]);
  const ultimaOuvida = useRef<EstadoGravacao | null>(null);
  useEffect(() => {
    if (gravacao.estado === "ouvida") {
      ultimaOuvida.current = gravacao;
      return;
    }
    const passada = ultimaOuvida.current;
    ultimaOuvida.current = null;
    if (passada?.estado === "ouvida" && passada.cartoes.length > 0) {
      setAnteriores((atual) => [...atual, ...passada.cartoes]);
    }
  }, [gravacao]);
  const atuais = gravacao.estado === "ouvida" ? gravacao.cartoes : [];
  const usando = gravacao.estado === "ouvida" ? gravacao.usando : null;
  // Quantas falas desta conversa já começaram a tocar: conta a partir de quando
  // ela começou (antes do "ouvido", a gravação passa por gravando/enviando).
  const falasAntes = useRef(0);
  useEffect(() => {
    if (gravacao.estado !== "ouvida") falasAntes.current = voz.falas;
  }, [gravacao.estado, voz.falas]);
  const falasTocadas = voz.temEnvelope ? voz.falas - falasAntes.current : null;
  // O cartão só sobe quando a fala dele começa; antes disso (e com uma ferramenta
  // rodando, quando o centro é do cartão de progresso) ele espera escondido.
  const momento =
    fase === "espera" ? "espera" : fase === "falando" && !usando ? "falando" : "trabalhando";
  const mostrados =
    momento === "espera"
      ? atuais
      : cartoesJaFalados(
          atuais,
          gravacao.estado === "ouvida" ? gravacao.falaDoCartao : [],
          falasTocadas,
        );
  const { destaque, fila } = arrumarCartoes(anteriores, mostrados, momento);
  // Numeração da sessão inteira: o destaque é sempre o último; a fileira vem antes.
  const fimDaFila = anteriores.length + mostrados.length - (destaque ? 1 : 0);

  const ultimaLatencia = latencias[latencias.length - 1];
  const ativas = habilidades.filter((h) => h.situacao === "pronta").length;

  return (
    <main className={`comando comando--${nucleo.tom} comando--${fase}`}>
      <header className="comando__manchete">
        <p className="comando__estado" role="status">
          {manchete}
        </p>
        <p className="comando__sublinha">{sublinha}</p>
      </header>

      <section className="comando__centro">
        <div className="comando__nucleo">
          <Nucleo
            niveis={[nivel, voz.nivel]}
            tom={ouvindoPedido ? "ok" : nucleo.tom}
            modo={ouvindoPedido ? "ouvindo" : modo}
          />
          {/* O assunto do momento, na frente do orbe. */}
          <div className="comando__destaque">
            {usando ? (
              <CartaoProgresso key={`usando-${usando}`} ferramenta={usando} />
            ) : (
              destaque && (
                <CartaoDestaque key={fimDaFila + 1} cartao={destaque} numero={fimDaFila + 1} />
              )
            )}
          </div>
        </div>
        {/* A legenda: a sua frase pequena e a fala dele grande, como num filme.
            Fala longa mostra só as últimas linhas, as de cima vão sumindo. */}
        <div className="comando__legenda">
          {falaOuvida && (
            <p className="comando__voce">
              <span className="comando__quem">{"Você ›"}</span> {detalhe}
            </p>
          )}
          {resposta && (
            <div className="comando__resposta">
              <p>
                {respostaVisivel}
                <span className="comando__cursor" aria-hidden="true" />
              </p>
            </div>
          )}
        </div>
      </section>

      {/* A fileira da sessão: faixa própria acima da barra de digitar, longe do
          orbe. O espaço fica reservado mesmo vazia, para o orbe não pular. */}
      <div className="comando__fila" aria-label="Cartões desta sessão">
        {fila.map((cartao, i) => {
          const numero = fimDaFila - fila.length + i + 1;
          return <CartaoMini key={numero} cartao={cartao} numero={numero} />;
        })}
      </div>

      <aside className="comando__cantos comando__cantos--esquerda">
        <Canto
          rotulo="Sistema"
          valor={
            <>
              <span className="canto__ponto" aria-hidden="true" />
              {ultimaLatencia === undefined ? "Online" : `${ultimaLatencia} ms`}
            </>
          }
          detalhe={`Sessão ${duracaoDesde(desbloqueadoEm, agora)}`}
          lado="esquerda"
          altura="topo"
          aberto={cantoAberto === "sistema"}
          onAlternar={alternar("sistema")}
        >
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
        </Canto>
        <Canto
          rotulo="Lembretes"
          valor={resumoDosLembretes(lembretes, agora)}
          lado="esquerda"
          altura="base"
          aberto={cantoAberto === "lembretes"}
          onAlternar={alternar("lembretes")}
        >
          <ModuloLembretes lembretes={lembretes} agora={agora} />
        </Canto>
      </aside>

      <aside className="comando__cantos comando__cantos--direita">
        <Canto
          rotulo="Tempo"
          valor={formatarHora(agora)}
          detalhe={formatarData(agora)}
          lado="direita"
          altura="topo"
          aberto={cantoAberto === "tempo"}
          onAlternar={alternar("tempo")}
        >
          <ModuloTempo agora={agora} />
        </Canto>
        <Canto
          rotulo="Habilidades"
          valor={`${ativas}/${habilidades.length} ativas`}
          lado="direita"
          altura="base"
          aberto={cantoAberto === "habilidades"}
          onAlternar={alternar("habilidades")}
        >
          <ModuloHabilidades habilidades={habilidades} />
        </Canto>
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
            placeholder={
              escuta.estado === "ouvindo"
                ? "Digite para o Jarvis… ou diga “Jarvis”"
                : "Digite para o Jarvis… ou segure ESPAÇO para falar"
            }
            maxLength={500}
            aria-label="Mensagem para o Jarvis"
          />
        </form>
        <OndaVoz niveis={[nivel, voz.nivel]} cor={CORES[nucleo.tom]} />
        <BotaoDaEscuta escuta={escuta} />
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

const TEXTO_DA_ESCUTA = {
  desligada: "Escuta off",
  ligando: "Escuta…",
  ouvindo: "Escuta on",
  indisponivel: "Escuta —",
  erro: "Escuta !",
} as const;

/** Liga e desliga a escuta sem tecla. Mostra quando ele está prestando atenção. */
function BotaoDaEscuta({ escuta }: { escuta: Escuta }) {
  const atento = escuta.atencao !== null;
  const dica =
    escuta.motivo ??
    (escuta.ligada
      ? "Escuta ligada: diga “Jarvis”. Clique para desligar o microfone."
      : "Escuta desligada. Clique para chamar o Jarvis pelo nome.");
  return (
    <button
      type="button"
      className={`comando__escuta comando__escuta--${atento ? "atenta" : escuta.estado}`}
      onClick={escuta.alternar}
      title={dica}
      aria-pressed={escuta.ligada}
    >
      <span className="comando__escuta-luz" aria-hidden="true" />
      {atento ? "Ouvindo" : TEXTO_DA_ESCUTA[escuta.estado]}
    </button>
  );
}
