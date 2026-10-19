import { useEffect, useState } from "react";

type EstadoNucleo = "pronto" | "ouvindo";

const capacidades = [
  { codigo: "01", nome: "Identidade", detalhe: "Reconhecimento facial", estado: "ATIVO", tom: "verde" },
  { codigo: "02", nome: "Voz", detalhe: "Canal de interação", estado: "PRONTO", tom: "azul" },
  { codigo: "03", nome: "Contexto", detalhe: "Memória da sessão", estado: "EM BREVE", tom: "neutro" },
];

function formatarHora(data: Date) {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(data);
}

function formatarData(data: Date) {
  return new Intl.DateTimeFormat("pt-BR", {
    weekday: "long",
    day: "2-digit",
    month: "long",
  }).format(data);
}

export function DashboardPrototipo() {
  const [agora, setAgora] = useState(() => new Date());
  const [estado, setEstado] = useState<EstadoNucleo>("pronto");

  useEffect(() => {
    const temporizador = window.setInterval(() => setAgora(new Date()), 1000);
    return () => window.clearInterval(temporizador);
  }, []);

  useEffect(() => {
    function lidarComTeclado(evento: KeyboardEvent) {
      if (evento.code !== "Space" || evento.repeat || evento.target instanceof HTMLInputElement) return;
      evento.preventDefault();
      setEstado((atual) => atual === "pronto" ? "ouvindo" : "pronto");
    }

    window.addEventListener("keydown", lidarComTeclado);
    return () => window.removeEventListener("keydown", lidarComTeclado);
  }, []);

  const ouvindo = estado === "ouvindo";

  return (
    <main className={`prototipo prototipo--${estado}`}>
      <div className="prototipo__grade" aria-hidden="true" />
      <div className="prototipo__varredura" aria-hidden="true" />

      <header className="prototipo__topo">
        <div className="prototipo__marca">
          <span className="prototipo__reator" aria-hidden="true" />
          <span>J.A.R.V.I.S.</span>
          <small>COMMAND INTERFACE</small>
        </div>
        <nav className="prototipo__nav" aria-label="Navegação do protótipo">
          <a className="prototipo__nav-link prototipo__nav-link--ativo" href="#nucleo">Núcleo</a>
          <a className="prototipo__nav-link" href="#capacidades">Capacidades</a>
          <a className="prototipo__nav-link" href="#atividade">Atividade</a>
        </nav>
        <div className="prototipo__sessao">
          <span className="prototipo__online"><i /> ONLINE</span>
          <span className="prototipo__sessao-separador" aria-hidden="true" />
          <span>BENEDITO</span>
        </div>
      </header>

      <section className="prototipo__intro" id="nucleo">
        <div>
          <p className="prototipo__eyebrow">NÚCLEO OPERACIONAL / 01</p>
          <h1>Boa noite, <strong>Benedito</strong>.</h1>
          <p className="prototipo__data">{formatarData(agora)} <span>·</span> sessão protegida</p>
        </div>
        <time className="prototipo__hora" dateTime={agora.toISOString()}>{formatarHora(agora)}</time>
      </section>

      <section className="prototipo__principal" aria-label="Núcleo operacional">
        <article className="prototipo__nucleo">
          <div className="prototipo__nucleo-cabecalho">
            <span>JARVIS / CORE</span>
            <span className="prototipo__telemetria">SYNC 100%</span>
          </div>

          <div className="prototipo__orbita" aria-hidden="true">
            <div className="prototipo__orbita-anel prototipo__orbita-anel--externo" />
            <div className="prototipo__orbita-anel prototipo__orbita-anel--interno" />
            <div className="prototipo__orbita-pontos" />
            <div className="prototipo__nucleo-luz">
              <span>J</span>
            </div>
            <div className="prototipo__onda">
              {[18, 30, 44, 25, 55, 34, 21, 40, 28, 50, 23, 37, 17].map((altura, indice) => (
                <i key={indice} style={{ height: `${ouvindo ? altura + 12 : altura * 0.38}px` }} />
              ))}
            </div>
          </div>

          <div className="prototipo__nucleo-estado">
            <div>
              <span className={`prototipo__estado-ponto ${ouvindo ? "prototipo__estado-ponto--ouvindo" : ""}`} />
              <strong>{ouvindo ? "Ouvindo você" : "Pronto para ouvir"}</strong>
            </div>
            <small>{ouvindo ? "Canal de voz aberto · fale agora" : "Pressione ESPAÇO para iniciar uma conversa"}</small>
          </div>

          <button className="prototipo__comando" type="button" onClick={() => setEstado(ouvindo ? "pronto" : "ouvindo")}>
            <span className="prototipo__comando-icone">{ouvindo ? "■" : "↓"}</span>
            <span>{ouvindo ? "Encerrar escuta" : "Ativar voz"}</span>
          </button>
        </article>

        <aside className="prototipo__status" aria-label="Status da sessão">
          <div className="prototipo__painel-cabecalho">
            <span className="prototipo__eyebrow">TELEMETRIA</span>
            <span className="prototipo__painel-codigo">LIVE</span>
          </div>
          <div className="prototipo__status-hero">
            <span className="prototipo__status-sinal" />
            <div>
              <strong>Sistema estável</strong>
              <small>Todos os canais respondendo</small>
            </div>
          </div>
          <dl className="prototipo__leituras">
            <div><dt>Sessão</dt><dd>PROTEGIDA</dd></div>
            <div><dt>Backend</dt><dd>ONLINE</dd></div>
            <div><dt>Identidade</dt><dd>BENEDITO</dd></div>
            <div><dt>Latência</dt><dd>24 ms</dd></div>
          </dl>
          <button className="prototipo__seguranca" type="button">
            <span>◈</span> Gerenciar segurança <b>↗</b>
          </button>
        </aside>
      </section>

      <section className="prototipo__inferior">
        <article className="prototipo__painel prototipo__painel--capacidades" id="capacidades">
          <div className="prototipo__painel-cabecalho">
            <span className="prototipo__eyebrow">CAPACIDADES</span>
            <span className="prototipo__painel-codigo">03 MÓDULOS</span>
          </div>
          <div className="prototipo__capacidades">
            {capacidades.map((capacidade) => (
              <div className="prototipo__capacidade" key={capacidade.codigo}>
                <span className="prototipo__capacidade-codigo">{capacidade.codigo}</span>
                <div><strong>{capacidade.nome}</strong><small>{capacidade.detalhe}</small></div>
                <span className={`prototipo__capacidade-estado prototipo__capacidade-estado--${capacidade.tom}`}>
                  {capacidade.estado}
                </span>
              </div>
            ))}
          </div>
        </article>

        <article className="prototipo__painel prototipo__painel--atividade" id="atividade">
          <div className="prototipo__painel-cabecalho">
            <span className="prototipo__eyebrow">ATIVIDADE RECENTE</span>
            <span className="prototipo__painel-codigo">HOJE</span>
          </div>
          <div className="prototipo__atividade-vazia">
            <span className="prototipo__atividade-linha" aria-hidden="true" />
            <div><strong>Nenhuma interação registrada</strong><small>Ative a voz para iniciar a sessão.</small></div>
          </div>
        </article>
      </section>

      <footer className="prototipo__rodape">
        <span>J.A.R.V.I.S. / PROTÓTIPO DE INTERFACE</span>
        <span>DESIGN STUDY · 2026</span>
      </footer>
    </main>
  );
}
