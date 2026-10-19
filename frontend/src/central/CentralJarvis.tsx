import { useEffect, useRef, useState } from "react";

type EstadoCentral = "standby" | "ouvindo" | "processando" | "respondendo";
type Mensagem = { id: number; autor: "jarvis" | "benedito"; texto: string; hora: string };

const ONDAS = [16, 23, 34, 47, 30, 64, 42, 77, 55, 90, 61, 82, 42, 70, 35, 58, 27, 43, 20, 13];
const FORMATO_HORA = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });
const FORMATO_DATA = new Intl.DateTimeFormat("pt-BR", { weekday: "long", day: "numeric", month: "long" });

function agora() {
  const data = new Date();
  return { hora: FORMATO_HORA.format(data), data: FORMATO_DATA.format(data) };
}

const ESTADOS: Record<EstadoCentral, { titulo: string; detalhe: string }> = {
  standby: { titulo: "À sua disposição", detalhe: "Diga o que precisa." },
  ouvindo: { titulo: "Estou ouvindo", detalhe: "Pode falar, senhor Benedito." },
  processando: { titulo: "Um instante", detalhe: "Estou organizando sua solicitação." },
  respondendo: { titulo: "Entendido", detalhe: "A prévia da conversa foi atualizada." },
};

export function CentralJarvis() {
  const [estado, setEstado] = useState<EstadoCentral>("standby");
  const [relogio, setRelogio] = useState(agora);
  const [entrada, setEntrada] = useState("");
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [mostraNota, setMostraNota] = useState(false);
  const timer = useRef<number | undefined>(undefined);
  const idMensagem = useRef(0);
  const ouvindo = estado === "ouvindo";

  useEffect(() => {
    const intervalo = window.setInterval(() => setRelogio(agora()), 1000);
    return () => window.clearInterval(intervalo);
  }, []);

  useEffect(() => () => window.clearTimeout(timer.current), []);

  const escreverMensagem = (autor: Mensagem["autor"], texto: string) => {
    idMensagem.current += 1;
    setMensagens((atuais) => [...atuais, { id: idMensagem.current, autor, texto, hora: FORMATO_HORA.format(new Date()) }]);
  };

  const responder = (texto: string) => {
    const pedido = texto.trim();
    if (!pedido) return;
    window.clearTimeout(timer.current);
    setEntrada("");
    setMostraNota(true);
    escreverMensagem("benedito", pedido);
    setEstado("processando");
    timer.current = window.setTimeout(() => {
      escreverMensagem("jarvis", "Entendido, senhor Benedito. Esta prévia demonstra a conversa; a execução de comandos será conectada ao sistema nas próximas etapas.");
      setEstado("respondendo");
      timer.current = window.setTimeout(() => setEstado("standby"), 2800);
    }, 950);
  };

  const iniciarEscuta = () => {
    if (estado === "processando" || estado === "respondendo") return;
    window.clearTimeout(timer.current);
    setEstado("ouvindo");
  };

  const concluirEscuta = () => {
    if (!ouvindo) return;
    escreverMensagem("benedito", "Comando de voz recebido (demonstração)");
    responderVoz();
  };

  const responderVoz = () => {
    setMostraNota(true);
    setEstado("processando");
    timer.current = window.setTimeout(() => {
      escreverMensagem("jarvis", "Recebi seu comando. A captura de voz real será ligada a esta interface depois da aprovação do design.");
      setEstado("respondendo");
      timer.current = window.setTimeout(() => setEstado("standby"), 2800);
    }, 950);
  };

  useEffect(() => {
    const aoPressionar = (event: KeyboardEvent) => {
      if (event.code !== "Space" || event.repeat) return;
      const alvo = event.target as HTMLElement | null;
      if (alvo?.tagName === "INPUT" || alvo?.tagName === "TEXTAREA" || alvo?.isContentEditable) return;
      event.preventDefault();
      iniciarEscuta();
    };
    const aoSoltar = (event: KeyboardEvent) => {
      if (event.code !== "Space") return;
      event.preventDefault();
      concluirEscuta();
    };
    const aoPerderFoco = () => concluirEscuta();
    window.addEventListener("keydown", aoPressionar);
    window.addEventListener("keyup", aoSoltar);
    window.addEventListener("blur", aoPerderFoco);
    return () => {
      window.removeEventListener("keydown", aoPressionar);
      window.removeEventListener("keyup", aoSoltar);
      window.removeEventListener("blur", aoPerderFoco);
    };
  }, [estado]);

  const alternarMicrofone = () => ouvindo ? concluirEscuta() : iniciarEscuta();

  return (
    <main className={`central central--${estado}`}>
      <div className="central__atmosfera" aria-hidden="true" />
      <div className="central__grade" aria-hidden="true" />
      <div className="central__particulas" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>

      <header className="central__topo">
        <div className="marca">
          <span className="marca__reator" aria-hidden="true"><i /></span>
          <span className="marca__nome">J.A.R.V.I.S.</span>
          <span className="marca__versao">PERSONAL INTELLIGENCE</span>
        </div>
        <div className="topo__identidade"><span className="topo__ponto" /> Sessão de Benedito <span className="topo__separador" /> {relogio.hora}</div>
      </header>

      <section className="central__campo" aria-label="Central de comando do J.A.R.V.I.S.">
        <div className="campo__fundo" aria-hidden="true">
          <span className="fundo__arco fundo__arco--um" />
          <span className="fundo__arco fundo__arco--dois" />
          <span className="fundo__linha" />
          <span className="fundo__coordenada">31° 45′ 43″ S&nbsp;&nbsp; 52° 20′ 11″ W</span>
        </div>

        <aside className="painel painel--contexto" aria-label="Contexto">
          <div className="painel__sobretitulo"><span>CONTEXTO</span><i>LOCAL</i></div>
          <time className="contexto__hora">{relogio.hora}</time>
          <p className="contexto__data">{relogio.data}</p>
          <div className="contexto__regua"><span /></div>
          <div className="contexto__linha"><span>perfil</span><b>Benedito</b></div>
          <div className="contexto__linha"><span>sessão</span><b>privada</b></div>
          <div className="contexto__linha"><span>entrada</span><b>{ouvindo ? "voz ativa" : "sob demanda"}</b></div>
        </aside>

        <section className="conversa" aria-live="polite" aria-label="Conversa com J.A.R.V.I.S.">
          <div className="conversa__topo">
            <div className="conversa__titulo"><span className="conversa__ponto" /><div><small>CANAL PARTICULAR</small><strong>Conversa</strong></div></div>
            <div className="conversa__data">{relogio.data}</div>
          </div>
          <div className="conversa__corpo">
            <div className="fala fala--jarvis fala--boas-vindas">
              <span className="fala__assinatura"><i>J</i> J.A.R.V.I.S.</span>
              <p>{mensagens.length ? ESTADOS[estado].titulo + ", senhor Benedito." : "Boa noite, senhor Benedito."}</p>
              <small>{mensagens.length ? ESTADOS[estado].detalhe : "Estou à sua disposição. O que vamos fazer?"}</small>
            </div>
            {mensagens.slice(-3).map((mensagem) => (
              <div className={`fala fala--${mensagem.autor}`} key={mensagem.id}>
                <span className="fala__assinatura">{mensagem.autor === "jarvis" ? "J.A.R.V.I.S." : "BENEDITO"}<time>{mensagem.hora}</time></span>
                <p>{mensagem.texto}</p>
              </div>
            ))}
            {estado === "processando" && <div className="conversa__processo"><span /><span /><span /> J.A.R.V.I.S. está compondo uma resposta</div>}
          </div>
          <form className="entrada" onSubmit={(event) => { event.preventDefault(); responder(entrada); }}>
            <span className="entrada__cursor" aria-hidden="true">›</span>
            <input value={entrada} onChange={(event) => setEntrada(event.target.value)} placeholder="Escreva uma instrução…" aria-label="Escreva uma instrução para J.A.R.V.I.S." />
            <button type="submit" aria-label="Enviar instrução" disabled={!entrada.trim()}>↗</button>
          </form>
          {mostraNota && <p className="conversa__nota">Prévia de interface · nenhuma ação foi executada</p>}
        </section>

        <aside className="painel painel--identidade" aria-label="Identidade da sessão">
          <div className="painel__sobretitulo"><span>IDENTIDADE</span><i>VERIFICADA</i></div>
          <div className="identidade__grafico" aria-hidden="true"><span className="identidade__circulo"><i>B</i></span><span className="identidade__orbita" /><span className="identidade__marcador" /></div>
          <strong className="identidade__nome">Benedito</strong>
          <span className="identidade__estado"><i /> Perfil ativo</span>
        </aside>

        <aside className="painel painel--sistema" aria-label="Estado da interface">
          <div className="painel__sobretitulo"><span>J.A.R.V.I.S.</span><i>{estado === "standby" ? "PRONTO" : "ATIVO"}</i></div>
          <div className="sistema__onda" aria-hidden="true">{ONDAS.slice(0, 15).map((altura, indice) => <i key={indice} style={{ "--onda": `${altura}%`, "--atraso": `${indice * 50}ms` } as React.CSSProperties} />)}</div>
          <div className="sistema__texto"><span className="sistema__ponto" /><div><strong>{ESTADOS[estado].titulo}</strong><small>{estado === "standby" ? "Canal em espera" : ESTADOS[estado].detalhe}</small></div></div>
        </aside>

        <div className="campo__legenda campo__legenda--esquerda"><span>INTERFACE DE COMANDO</span><i>LOCAL / 01</i></div>
        <div className="campo__legenda campo__legenda--direita">{relogio.data.toUpperCase()}</div>
      </section>

      <footer className="central__comando">
        <div className="comando__marca"><span className="comando__ponto" /><div><small>CANAL DE VOZ</small><strong>{ouvindo ? "Estou ouvindo…" : estado === "processando" ? "Organizando a resposta…" : "Fale com J.A.R.V.I.S."}</strong></div></div>
        <button type="button" className="comando__microfone" onClick={alternarMicrofone} aria-label={ouvindo ? "Finalizar comando de voz" : "Iniciar comando de voz"} aria-pressed={ouvindo}>
          <span className="microfone__desenho" aria-hidden="true"><i /></span>
        </button>
        <div className="comando__ajuda"><span>SEGURE</span><kbd>ESPAÇO</kbd><span>PARA FALAR</span></div>
      </footer>
    </main>
  );
}
