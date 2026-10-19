import { useEffect, useState } from "react";

type EstadoPresenca = "disponivel" | "ouvindo";

const BARRAS = [10, 18, 26, 34, 22, 42, 30, 52, 36, 60, 42, 50, 30, 42, 24, 34, 18, 10];

function horarioAtual() {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date());
}

function dataAtual() {
  return new Intl.DateTimeFormat("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
  }).format(new Date());
}

export function PresencaJarvis() {
  const [estado, setEstado] = useState<EstadoPresenca>("disponivel");
  const [hora, setHora] = useState(horarioAtual);
  const ouvindo = estado === "ouvindo";

  useEffect(() => {
    const relogio = window.setInterval(() => setHora(horarioAtual()), 1000);
    return () => window.clearInterval(relogio);
  }, []);

  useEffect(() => {
    const aoPressionar = (event: KeyboardEvent) => {
      if (event.code !== "Space" || event.repeat) return;
      const alvo = event.target as HTMLElement | null;
      if (alvo?.tagName === "INPUT" || alvo?.tagName === "TEXTAREA") return;
      event.preventDefault();
      setEstado("ouvindo");
    };

    const aoSoltar = (event: KeyboardEvent) => {
      if (event.code !== "Space") return;
      event.preventDefault();
      setEstado("disponivel");
    };

    const aoPerderFoco = () => setEstado("disponivel");

    window.addEventListener("keydown", aoPressionar);
    window.addEventListener("keyup", aoSoltar);
    window.addEventListener("blur", aoPerderFoco);

    return () => {
      window.removeEventListener("keydown", aoPressionar);
      window.removeEventListener("keyup", aoSoltar);
      window.removeEventListener("blur", aoPerderFoco);
    };
  }, []);

  const alternarEscuta = () => setEstado((atual) => (atual === "ouvindo" ? "disponivel" : "ouvindo"));

  return (
    <main className={`presenca presenca--${estado}`}>
      <div className="presenca__atmosfera" aria-hidden="true" />

      <header className="presenca__topo">
        <div className="presenca__marca" aria-label="J.A.R.V.I.S.">
          <span className="presenca__marca-orbe" aria-hidden="true" />
          <span>J.A.R.V.I.S.</span>
        </div>

        <div className="presenca__sessao">
          <span className="presenca__online"><i aria-hidden="true" /> online</span>
          <span className="presenca__divisor" aria-hidden="true" />
          <span>Benedito</span>
        </div>
      </header>

      <section className="presenca__centro" aria-live="polite">
        <div className="presenca__saudacao">
          <p className="presenca__eyebrow">J.A.R.V.I.S. está presente</p>
          <h1>Boa noite, <strong>Benedito</strong>.</h1>
          <p className="presenca__subtitulo">
            {ouvindo ? "Estou ouvindo você." : "Estou aqui. O que você precisa?"}
          </p>
          <p className="presenca__data">{dataAtual()}</p>
        </div>

        <div className="presenca__nucleo" aria-label={ouvindo ? "J.A.R.V.I.S. ouvindo" : "J.A.R.V.I.S. pronto para conversar"}>
          <div className="presenca__orbita presenca__orbita--externa" aria-hidden="true" />
          <div className="presenca__orbita presenca__orbita--interna" aria-hidden="true" />
          <div className="presenca__nucleo-luz" aria-hidden="true">
            <span>J</span>
          </div>
          <div className="presenca__onda" aria-hidden="true">
            {BARRAS.map((altura, indice) => (
              <span
                key={indice}
                style={{ "--altura": `${altura}%`, "--atraso": `${indice * 45}ms` } as React.CSSProperties}
              />
            ))}
          </div>
          <span className="presenca__estado">{ouvindo ? "ouvindo" : "pronto"}</span>
        </div>

        <div className="presenca__controle">
          <button
            type="button"
            className="presenca__botao"
            aria-pressed={ouvindo}
            onClick={alternarEscuta}
          >
            <span className="presenca__microfone" aria-hidden="true">
              <span />
            </span>
            <span className="presenca__botao-texto">
              <strong>{ouvindo ? "Escuta ativa" : "Falar com J.A.R.V.I.S."}</strong>
              <small>{ouvindo ? "Clique para encerrar" : "Segure a barra de espaço"}</small>
            </span>
            <span className="presenca__atalho" aria-hidden="true">space</span>
          </button>
        </div>
      </section>

      <footer className="presenca__rodape">
        <div className="presenca__sinal">
          <span className="presenca__sinal-ponto" aria-hidden="true" />
          <span>sessão protegida</span>
        </div>
        <div className="presenca__rodape-status">
          <span><b>identidade</b> reconhecida</span>
          <span><b>backend</b> online</span>
          <span className="presenca__hora">{hora}</span>
        </div>
      </footer>
    </main>
  );
}
