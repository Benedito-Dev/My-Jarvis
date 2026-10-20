import type { ReactNode } from "react";
import type { Habilidade, Lembrete } from "../api";
import { duracaoDesde, linhaDoGrafico, tempoAte } from "../modulos";
import { formatarData, formatarHora } from "../tempo";

// Os módulos das laterais da central de comando. Toda informação aqui é real e
// tem rótulo; molduras, cantoneiras e anéis girando são só enfeite.

/** A moldura de HUD: cantoneiras, cabeçalho numerado e um traço de varredura. */
function Modulo({
  indice,
  titulo,
  extra,
  children,
}: {
  indice: string;
  titulo: string;
  extra?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="modulo">
      {["no", "ne", "so", "se"].map((canto) => (
        <span key={canto} className={`modulo__canto modulo__canto--${canto}`} aria-hidden="true" />
      ))}
      <header className="modulo__cabecalho">
        <span className="modulo__indice" aria-hidden="true">
          {indice}
        </span>
        <h2 className="modulo__titulo">{titulo}</h2>
        <span className="modulo__traco" aria-hidden="true" />
        {extra && <span className="modulo__extra">{extra}</span>}
      </header>
      {children}
    </section>
  );
}

/**
 * Um canto do painel: um resumo pequeno (rótulo + valor) que, clicado, abre o
 * módulo inteiro por cima. Assim o centro fica livre para a conversa.
 */
export function Canto({
  rotulo,
  valor,
  detalhe,
  lado,
  altura,
  aberto,
  onAlternar,
  children,
}: {
  rotulo: string;
  valor: ReactNode;
  detalhe?: string;
  lado: "esquerda" | "direita";
  altura: "topo" | "base";
  aberto: boolean;
  onAlternar: () => void;
  children: ReactNode;
}) {
  return (
    <div className={`canto canto--${lado} canto--${altura} ${aberto ? "canto--aberto" : ""}`}>
      <button className="canto__resumo" type="button" onClick={onAlternar} aria-expanded={aberto}>
        <span className="canto__rotulo">{rotulo}</span>
        <span className="canto__valor">{valor}</span>
        {detalhe && <span className="canto__detalhe">{detalhe}</span>}
      </button>
      {aberto && <div className="canto__painel">{children}</div>}
    </div>
  );
}

// --- 01 · Sistema -------------------------------------------------------------

const GRAFICO = { largura: 160, altura: 28 };

type PropsSistema = {
  usuario: string;
  agora: Date;
  desbloqueadoEm: Date;
  latencias: number[];
  rostos: number;
  ouvindo: boolean;
  versao: string;
  onCadastrarRosto: () => void;
  onConfigurarPin: () => void;
};

export function ModuloSistema({
  usuario,
  agora,
  desbloqueadoEm,
  latencias,
  rostos,
  ouvindo,
  versao,
  onCadastrarRosto,
  onConfigurarPin,
}: PropsSistema) {
  const linha = linhaDoGrafico(latencias, GRAFICO.largura, GRAFICO.altura);
  const ultima = latencias[latencias.length - 1];

  return (
    <Modulo indice="01" titulo="Sistema" extra={`v${versao}`}>
      <div className="sinal">
        <div className="sinal__topo">
          <span className="sinal__ponto" aria-hidden="true" />
          <span className="sinal__rotulo">Backend</span>
          <span className="sinal__valor">Online</span>
        </div>
        <div className="sinal__grafico">
          <svg
            viewBox={`0 0 ${GRAFICO.largura} ${GRAFICO.altura}`}
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            {linha && (
              <>
                <polygon
                  className="sinal__area"
                  points={`0,${GRAFICO.altura} ${linha} ${GRAFICO.largura},${GRAFICO.altura}`}
                />
                <polyline className="sinal__linha" points={linha} />
              </>
            )}
          </svg>
          <span className="sinal__ms" title="Quanto o backend levou para responder">
            {ultima === undefined ? "—" : `${ultima} ms`}
          </span>
        </div>
        <span className="sinal__legenda">Latência · último minuto</span>
      </div>

      <div className="blocos">
        <Bloco rotulo="Operador" valor={usuario.toUpperCase()} />
        <Bloco rotulo="Sessão" valor={duracaoDesde(desbloqueadoEm, agora)} />
        <Bloco rotulo="Rostos" valor={String(rostos).padStart(2, "0")} />
        <Bloco rotulo="Microfone" valor={ouvindo ? "OUVINDO" : "LIVRE"} vivo={ouvindo} />
      </div>

      <div className="modulo__acoes">
        <button className="modulo__acao" type="button" onClick={onCadastrarRosto}>
          <IconeRosto /> Rosto
        </button>
        <button className="modulo__acao" type="button" onClick={onConfigurarPin}>
          <IconeChave /> PIN
        </button>
      </div>
    </Modulo>
  );
}

function Bloco({ rotulo, valor, vivo }: { rotulo: string; valor: string; vivo?: boolean }) {
  return (
    <div className={`bloco ${vivo ? "bloco--vivo" : ""}`}>
      <span className="bloco__rotulo">{rotulo}</span>
      <span className="bloco__valor">{valor}</span>
    </div>
  );
}

// --- 02 · Tempo -----------------------------------------------------------------

const VOLTA_SEGUNDOS = 2 * Math.PI * 26;

export function ModuloTempo({ agora }: { agora: Date }) {
  const segundos = agora.getSeconds();
  return (
    <Modulo indice="02" titulo="Tempo" extra="SÃO PAULO">
      <div className="tempo">
        {/* O anel enche ao longo do minuto: é o ponteiro dos segundos. */}
        <svg className="tempo__anel" viewBox="0 0 64 64" aria-hidden="true">
          <circle className="tempo__trilho" cx="32" cy="32" r="26" />
          <circle
            className="tempo__segundos"
            cx="32"
            cy="32"
            r="26"
            strokeDasharray={VOLTA_SEGUNDOS}
            strokeDashoffset={VOLTA_SEGUNDOS * (1 - segundos / 60)}
            transform="rotate(-90 32 32)"
          />
          <text className="tempo__seg-texto" x="32" y="36" textAnchor="middle">
            {String(segundos).padStart(2, "0")}
          </text>
        </svg>
        <div>
          <p className="tempo__hora">{formatarHora(agora)}</p>
          <p className="tempo__data">{formatarData(agora)}</p>
        </div>
      </div>
    </Modulo>
  );
}

// --- 03 · Habilidades -------------------------------------------------------------

export function ModuloHabilidades({ habilidades }: { habilidades: Habilidade[] }) {
  const ativas = habilidades.filter((h) => h.situacao === "pronta").length;
  return (
    <Modulo indice="03" titulo="Habilidades" extra={`${ativas}/${habilidades.length} ativas`}>
      <ul className="habilidades">
        {habilidades.map((habilidade) => (
          <li key={habilidade.id} className={`habilidade habilidade--${habilidade.situacao}`}>
            <span className="habilidade__icone" aria-hidden="true">
              <svg className="habilidade__anel" viewBox="0 0 40 40">
                <circle cx="20" cy="20" r="18" />
              </svg>
              <IconeHabilidade id={habilidade.id} />
            </span>
            <span className="habilidade__texto">
              <span className="habilidade__nome">{habilidade.nome}</span>
              <span className="habilidade__descricao">{habilidade.descricao}</span>
            </span>
            <span className="habilidade__situacao">
              {habilidade.situacao === "pronta" ? "Ativa" : "Em breve"}
            </span>
          </li>
        ))}
      </ul>
    </Modulo>
  );
}

// --- 04 · Lembretes ---------------------------------------------------------------

export function ModuloLembretes({ lembretes, agora }: { lembretes: Lembrete[]; agora: Date }) {
  return (
    <Modulo indice="04" titulo="Lembretes" extra={`${lembretes.length} ativos`}>
      {lembretes.length === 0 ? (
        <p className="lembretes__vazio">
          Nenhum. Diga: <em>“Jarvis, me lembra de... daqui a 10 minutos”</em>
        </p>
      ) : (
        <ul className="lembretes">
          {lembretes.map((lembrete) => {
            const quando = new Date(lembrete.quando);
            return (
              <li key={lembrete.id} className="lembrete">
                <span className="lembrete__icone" aria-hidden="true">
                  <IconeRelogio />
                </span>
                <span className="lembrete__texto">{lembrete.texto}</span>
                <span className="lembrete__quando">
                  <span className="lembrete__hora">{formatarHora(quando)}</span>
                  <span className="lembrete__falta">{tempoAte(quando, agora)}</span>
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </Modulo>
  );
}

// --- Ícones (traço fino, herdam a cor) ------------------------------------------

function IconeHabilidade({ id }: { id: string }) {
  if (id === "desbloqueio_facial") return <IconeRosto />;
  if (id === "voz") return <IconeVoz />;
  if (id === "conversa") return <IconeConversa />;
  return <IconeHexagono />;
}

const Svg = ({ children }: { children: ReactNode }) => (
  <svg className="icone" viewBox="0 0 24 24" aria-hidden="true">
    {children}
  </svg>
);

const IconeRosto = () => (
  <Svg>
    <path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3" />
    <path d="M9 10v1M15 10v1M12 10v3.5h-1M9.5 16.5a4 4 0 0 0 5 0" />
  </Svg>
);

const IconeVoz = () => (
  <Svg>
    <path d="M4 10v4M8 7v10M12 4v16M16 8v8M20 11v2" />
  </Svg>
);

const IconeConversa = () => (
  <Svg>
    <path d="M4 5h16v11H10l-5 4v-4H4z" />
    <path d="M8 10.5h.01M12 10.5h.01M16 10.5h.01" />
  </Svg>
);

const IconeChave = () => (
  <Svg>
    <circle cx="8" cy="15" r="4" />
    <path d="M11 12l8-8M16 7l3 3M14 9l2 2" />
  </Svg>
);

const IconeRelogio = () => (
  <Svg>
    <circle cx="12" cy="13" r="8" />
    <path d="M12 9v4l2.5 2.5M9 2h6M12 2v3" />
  </Svg>
);

const IconeHexagono = () => (
  <Svg>
    <path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z" />
  </Svg>
);
