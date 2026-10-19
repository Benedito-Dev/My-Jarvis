import { useEffect, useRef, useState } from "react";
import { AuraVisual } from "./AuraVisual";

type IconName = "home" | "cube" | "folder" | "calendar" | "chart" | "settings" | "weather" | "agenda" | "summary" | "focus" | "send" | "mic";
type Mensagem = { id: number; autor: "usuario" | "jarvis"; texto: string };

function Icone({ nome, tamanho = 22 }: { nome: IconName; tamanho?: number }) {
  const comum = { width: tamanho, height: tamanho, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 1.55, strokeLinecap: "round" as const, strokeLinejoin: "round" as const, "aria-hidden": true as const };
  const desenhos: Record<IconName, React.ReactNode> = {
    home: <><path d="m3.5 10 8.5-7 8.5 7" /><path d="M5.5 9v11h13V9M9.5 20v-6h5v6" /></>,
    cube: <><path d="m12 2.8 8.5 4.7v9L12 21.2l-8.5-4.7v-9L12 2.8Z" /><path d="m3.7 7.6 8.3 4.8 8.3-4.8M12 12.4v8.4" /></>,
    folder: <><path d="M3 6.5h7l2 2h9v9.8a1.7 1.7 0 0 1-1.7 1.7H4.7A1.7 1.7 0 0 1 3 18.3V6.5Z" /><path d="M3.2 9h17.5" /></>,
    calendar: <><rect x="3.5" y="5" width="17" height="16" rx="2" /><path d="M7.5 3v4M16.5 3v4M3.5 9.5h17" /><path d="m9.2 14 1.8 1.8 4-4" /></>,
    chart: <><path d="M4 19.5V4.5M4 19.5h17" /><path d="m7 15 4-4 3 2 5-6" /><path d="M16 7h3v3" /></>,
    settings: <><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path d="m19.3 13.8 1.1.9-1.4 2.4-1.4-.5a7.6 7.6 0 0 1-1.6.9l-.3 1.5h-2.8l-.3-1.5a7.6 7.6 0 0 1-1.6-.9l-1.4.5-1.4-2.4 1.1-.9a7.2 7.2 0 0 1 0-1.8l-1.1-.9 1.4-2.4 1.4.5a7.6 7.6 0 0 1 1.6-.9l.3-1.5h2.8l.3 1.5a7.6 7.6 0 0 1 1.6.9l1.4-.5 1.4 2.4-1.1.9a7.2 7.2 0 0 1 0 1.8Z" /></>,
    weather: <><path d="M8 18.5h10a4 4 0 0 0 .2-8A6.2 6.2 0 0 0 6.5 9a4.8 4.8 0 0 0 1.5 9.5Z" /><path d="M8.5 3v2M3.8 5l1.4 1.4M2.5 10h2" /></>,
    agenda: <><rect x="4" y="5" width="16" height="16" rx="2" /><path d="M8 3v4M16 3v4M4 9h16m-11 4h2m3 0h2m-7 4h2" /></>,
    summary: <><path d="M6 3.5h8l4 4v13H6a2 2 0 0 1-2-2v-13a2 2 0 0 1 2-2Z" /><path d="M14 3.8v4h4M8 12h8M8 16h6" /></>,
    focus: <><circle cx="12" cy="12" r="8.5" /><circle cx="12" cy="12" r="4.6" /><path d="M12 12 20 4m-4.5 0H20v4.5" /></>,
    send: <><path d="M12 19V5m-6 6 6-6 6 6" /></>,
    mic: <><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3m-4 0h8" /></>,
  };

  return <svg {...comum}>{desenhos[nome]}</svg>;
}

function formatarFoco(segundos: number) {
  return `${String(Math.floor(segundos / 60)).padStart(2, "0")}:${String(segundos % 60).padStart(2, "0")}`;
}

export function DashboardAura() {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [texto, setTexto] = useState("");
  const [ouvindo, setOuvindo] = useState(false);
  const [respondendo, setRespondendo] = useState(false);
  const [aviso, setAviso] = useState("");
  const [focoAtivo, setFocoAtivo] = useState(false);
  const [focoSegundos, setFocoSegundos] = useState(25 * 60);
  const contadorMensagens = useRef(0);
  const timerResposta = useRef<number | undefined>(undefined);
  const painelMensagens = useRef<HTMLDivElement>(null);

  useEffect(() => () => window.clearTimeout(timerResposta.current), []);

  useEffect(() => {
    if (!focoAtivo || focoSegundos <= 0) return;
    const timer = window.setInterval(() => {
      setFocoSegundos((restante) => Math.max(0, restante - 1));
    }, 1000);
    return () => window.clearInterval(timer);
  }, [focoAtivo, focoSegundos]);

  useEffect(() => {
    const painel = painelMensagens.current;
    if (painel) painel.scrollTo({ top: painel.scrollHeight, behavior: "smooth" });
  }, [mensagens, respondendo]);

  const enviar = (mensagem: string) => {
    const conteudo = mensagem.trim();
    if (!conteudo || respondendo) return;

    contadorMensagens.current += 1;
    setMensagens((atuais) => [...atuais, { id: contadorMensagens.current, autor: "usuario", texto: conteudo }]);
    setTexto("");
    setAviso("");
    setRespondendo(true);
    timerResposta.current = window.setTimeout(() => {
      contadorMensagens.current += 1;
      setMensagens((atuais) => [...atuais, {
        id: contadorMensagens.current,
        autor: "jarvis",
        texto: "A conversa com o modelo ainda será conectada. Esta resposta só demonstra o fluxo visual.",
      }]);
      setRespondendo(false);
    }, 550);
  };

  const agora = new Date();
  const hora = agora.getHours();
  const saudacao = hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite";
  const dataHoje = new Intl.DateTimeFormat("pt-BR", { weekday: "long", day: "numeric", month: "long" }).format(agora);

  const alternarFoco = () => {
    if (!focoAtivo && focoSegundos === 0) setFocoSegundos(25 * 60);
    setFocoAtivo((ativo) => !ativo);
    setAviso(focoAtivo ? "Foco pausado." : "Foco iniciado por 25 minutos.");
  };

  const alternarVoz = () => {
    setOuvindo((ativo) => !ativo);
    setAviso(ouvindo ? "Demonstração de voz encerrada." : "A captura de voz não está conectada nesta prévia.");
  };

  return (
    <main className={`aura-app${mensagens.length ? " aura-app--conversa" : ""}`}>
      <div className="aura-atmosfera" aria-hidden="true" />
      <div className="aura-piso" aria-hidden="true" />
      <AuraVisual />

      <nav className="aura-rail" aria-label="Navegação principal">
        <button className="aura-rail__item aura-rail__item--active" aria-label="Início" aria-current="page" title="Início" type="button">
          <Icone nome="home" />
          <i />
        </button>
        <button className="aura-rail__item" aria-label="Capacidades, demonstração visual" title="Capacidades" type="button" onClick={() => setAviso("Capacidades serão conectadas em outra etapa.")}><Icone nome="cube" /></button>
        <button className="aura-rail__item" aria-label="Projetos, demonstração visual" title="Projetos" type="button" onClick={() => setAviso("Projetos serão conectados em outra etapa.")}><Icone nome="folder" /></button>
        <button className="aura-rail__item" aria-label="Agenda, demonstração visual" title="Agenda" type="button" onClick={() => setAviso("A agenda mostrada é apenas ilustrativa.")}><Icone nome="calendar" /></button>
        <button className="aura-rail__item" aria-label="Atividade, demonstração visual" title="Atividade" type="button" onClick={() => setAviso("O histórico de atividade será conectado em outra etapa.")}><Icone nome="chart" /></button>
        <span className="aura-rail__divider" />
        <button className="aura-rail__item" aria-label="Configurações, demonstração visual" title="Configurações" type="button" onClick={() => setAviso("As configurações não fazem parte desta prévia.")}><Icone nome="settings" /></button>
      </nav>

      <header className="aura-topbar">
        <div className="aura-brandline">
          <span className="aura-wordmark">J A R V I S</span>
          <span className="aura-brandline__separator" />
          <span className="aura-brandline__edition">AURA <b>/</b> PRATA <b>/</b> PETRÓLEO</span>
        </div>
        <div className="aura-user"><i /> <span>Benedito</span><span className="aura-user__verified" aria-label="perfil autenticado">✓</span></div>
      </header>

      <section className={`aura-content${mensagens.length ? " aura-content--conversa" : ""}`} aria-label="Assistente J.A.R.V.I.S.">
        {mensagens.length === 0 ? (
          <div className="aura-home">
            <p className="aura-home__date">{dataHoje} <span>·</span> sessão pessoal</p>
            <h1>{saudacao}, <span>Benedito.</span></h1>
            <p className="aura-home__subtitle">Seu dia, com mais clareza.</p>

            <div className="aura-glance" aria-label="Resumo demonstrativo do dia">
              <div className="aura-glance__row">
                <span className="aura-glance__icon"><Icone nome="weather" tamanho={40} /></span>
                <div className="aura-glance__copy">
                  <p>Fortaleza <span>·</span> 28°</p>
                  <small>Parcialmente nublado</small>
                </div>
                <span className="aura-demo-tag">EXEMPLO</span>
              </div>
              <div className="aura-glance__row">
                <span className="aura-glance__icon"><Icone nome="agenda" tamanho={38} /></span>
                <div className="aura-glance__copy">
                  <p><span className="aura-event-time">09:00</span> Revisar projeto</p>
                  <small>Projeto Atlas <span>·</span> Sala virtual</small>
                </div>
                <span className="aura-demo-tag">EXEMPLO</span>
              </div>
            </div>

            <div className="aura-actions" aria-label="Ações rápidas">
              <button type="button" className="aura-action" onClick={() => enviar("Resuma meu dia") }>
                <Icone nome="summary" tamanho={20} />
                <span>Resumir meu dia</span>
              </button>
              <button type="button" className={`aura-action${focoAtivo ? " aura-action--active" : ""}`} onClick={alternarFoco}>
                <Icone nome="focus" tamanho={20} />
                <span>{focoAtivo ? `Foco · ${formatarFoco(focoSegundos)}` : "Iniciar foco"}</span>
              </button>
              <button type="button" className="aura-action" onClick={() => setAviso("Projetos ainda não estão conectados nesta prévia.")}>
                <Icone nome="folder" tamanho={20} />
                <span>Abrir projetos</span>
              </button>
            </div>
            <p className="aura-home__note">Clima e agenda são exemplos visuais nesta prévia.</p>
          </div>
        ) : (
          <div className="aura-messages" ref={painelMensagens} aria-live="polite">
            {mensagens.map((mensagem) => (
              <article className={`aura-message aura-message--${mensagem.autor}`} key={mensagem.id}>
                {mensagem.autor === "jarvis" && <span className="aura-message__name">J.A.R.V.I.S.</span>}
                <p>{mensagem.texto}</p>
              </article>
            ))}
            {respondendo && <p className="aura-thinking" aria-label="J.A.R.V.I.S. está respondendo"><i /><i /><i /></p>}
          </div>
        )}
      </section>

      <div className="aura-compose-wrap">
        <form className="aura-compose" onSubmit={(event) => { event.preventDefault(); enviar(texto); }}>
          <button type="button" className={`aura-compose__mic${ouvindo ? " aura-compose__mic--active" : ""}`} onClick={alternarVoz} aria-label={ouvindo ? "Encerrar demonstração de voz" : "Ativar demonstração de voz"} aria-pressed={ouvindo}>
            <Icone nome="mic" tamanho={25} />
          </button>
          <textarea
            value={texto}
            onChange={(event) => setTexto(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                enviar(texto);
              }
            }}
            placeholder={ouvindo ? "Demonstração de voz ativa" : "Pergunte ou peça alguma coisa…"}
            aria-label="Mensagem para J.A.R.V.I.S."
            rows={1}
          />
          <div className="aura-wave" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
          <button type="submit" className="aura-compose__send" disabled={!texto.trim() || respondendo} aria-label="Enviar mensagem"><Icone nome="send" tamanho={21} /></button>
        </form>
        <div className="aura-compose-meta">
          <span>{aviso || "J.A.R.V.I.S. · prévia de interface"}</span>
          <span>Enter para enviar <b>·</b> Shift + Enter para nova linha</span>
        </div>
      </div>
    </main>
  );
}
