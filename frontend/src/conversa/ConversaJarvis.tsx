import { useEffect, useRef, useState } from "react";

type Mensagem = { id: number; autor: "usuario" | "jarvis"; texto: string };

export function ConversaJarvis() {
  const [mensagens, setMensagens] = useState<Mensagem[]>([]);
  const [texto, setTexto] = useState("");
  const [ouvindo, setOuvindo] = useState(false);
  const [respondendo, setRespondendo] = useState(false);
  const id = useRef(0);
  const respostaTimer = useRef<number | undefined>(undefined);

  useEffect(() => () => window.clearTimeout(respostaTimer.current), []);

  const enviar = (mensagem: string) => {
    const conteudo = mensagem.trim();
    if (!conteudo || respondendo) return;

    id.current += 1;
    setMensagens((atuais) => [...atuais, { id: id.current, autor: "usuario", texto: conteudo }]);
    setTexto("");
    setRespondendo(true);
    respostaTimer.current = window.setTimeout(() => {
      id.current += 1;
      setMensagens((atuais) => [...atuais, {
        id: id.current,
        autor: "jarvis",
        texto: "Esta é uma prévia da interface. A conexão com o modelo de conversa ainda não está configurada.",
      }]);
      setRespondendo(false);
    }, 650);
  };

  useEffect(() => {
    const teclaPressionada = (event: KeyboardEvent) => {
      const alvo = event.target as HTMLElement | null;
      if (event.code !== "Space" || event.repeat || alvo?.tagName === "TEXTAREA" || alvo?.tagName === "INPUT") return;
      event.preventDefault();
      setOuvindo(true);
    };
    const teclaSolta = (event: KeyboardEvent) => {
      if (event.code === "Space") setOuvindo(false);
    };
    const perdeuFoco = () => setOuvindo(false);
    window.addEventListener("keydown", teclaPressionada);
    window.addEventListener("keyup", teclaSolta);
    window.addEventListener("blur", perdeuFoco);
    return () => {
      window.removeEventListener("keydown", teclaPressionada);
      window.removeEventListener("keyup", teclaSolta);
      window.removeEventListener("blur", perdeuFoco);
    };
  }, []);

  return (
    <main className="conversa-app">
      <header className="conversa-topbar">
        <div className="conversa-brand" aria-label="J.A.R.V.I.S.">
          <span className="conversa-brand__mark">J</span>
          <span>J.A.R.V.I.S.</span>
        </div>
        <div className="conversa-account">
          <span className="conversa-online"><i /> online</span>
          <span className="conversa-account__separator" />
          <span>Benedito</span>
        </div>
      </header>

      <section className={`conversa-main${mensagens.length ? " conversa-main--ativa" : ""}`} aria-label="Conversa com J.A.R.V.I.S.">
        {mensagens.length === 0 ? (
          <div className="conversa-welcome">
            <p className="conversa-welcome__greeting">Boa noite, <span>Benedito</span>.</p>
            <h1>Como posso ajudar?</h1>
          </div>
        ) : (
          <div className="conversa-mensagens" aria-live="polite">
            {mensagens.map((mensagem) => (
              <article className={`mensagem mensagem--${mensagem.autor}`} key={mensagem.id}>
                {mensagem.autor === "jarvis" && <span className="mensagem__autor">J.A.R.V.I.S.</span>}
                <p>{mensagem.texto}</p>
              </article>
            ))}
            {respondendo && <p className="conversa-aguardando" aria-label="J.A.R.V.I.S. está respondendo"><i /><i /><i /></p>}
          </div>
        )}

        <div className="conversa-compose-wrap">
          <form className="conversa-compose" onSubmit={(event) => { event.preventDefault(); enviar(texto); }}>
            <textarea
              value={texto}
              onChange={(event) => setTexto(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  enviar(texto);
                }
              }}
              placeholder={ouvindo ? "Ouvindo…" : "Converse com J.A.R.V.I.S."}
              aria-label="Mensagem para J.A.R.V.I.S."
              rows={1}
            />
            <div className="conversa-compose__actions">
              <span className="conversa-compose__hint">{ouvindo ? "Escuta demonstrativa" : "Enter para enviar · Shift + Enter para nova linha"}</span>
              <div className="conversa-compose__buttons">
                <button type="button" className={`botao-voz${ouvindo ? " botao-voz--ativo" : ""}`} onClick={() => setOuvindo((valor) => !valor)} aria-label={ouvindo ? "Parar demonstração de voz" : "Ativar demonstração de voz"} aria-pressed={ouvindo}>
                  <svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3" /><path d="M5.5 11.5a6.5 6.5 0 0 0 13 0M12 18v3m-4 0h8" /></svg>
                </button>
                <button type="submit" className="botao-enviar" disabled={!texto.trim() || respondendo} aria-label="Enviar mensagem">
                  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5m-6 6 6-6 6 6" /></svg>
                </button>
              </div>
            </div>
          </form>
          <p className="conversa-compose__disclaimer">J.A.R.V.I.S. pode cometer erros. Confira informações importantes.</p>
        </div>
      </section>
    </main>
  );
}
