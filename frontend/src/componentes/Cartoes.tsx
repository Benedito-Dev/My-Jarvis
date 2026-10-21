import { type Cartao, fraseDaFerramenta, resumoDoCartao } from "../cartoes";

// Os cartões da conversa: o grande, na frente do orbe, com o assunto do momento;
// os pequenos, na fileira de baixo, com o que já foi dito; e o de progresso,
// enquanto uma ferramenta roda ("Consultando o clima...").

/** O cartão em destaque: cabeçalho comum e um corpo próprio de cada tipo. */
export function CartaoDestaque({ cartao, numero }: { cartao: Cartao; numero: number }) {
  return (
    <article className={`cartao cartao--${cartao.tipo}`}>
      <header className="cartao__cabecalho">
        <span className="cartao__numero">{String(numero).padStart(2, "0")}</span>
        <span className="cartao__rotulo">{cartao.rotulo}</span>
      </header>
      <h3 className="cartao__titulo">{cartao.titulo}</h3>
      <CorpoDoCartao cartao={cartao} />
    </article>
  );
}

function CorpoDoCartao({ cartao }: { cartao: Cartao }) {
  switch (cartao.tipo) {
    case "clima":
      return (
        <>
          <div className="clima">
            <p className="clima__temperatura">
              {cartao.temperatura}
              <span>°</span>
            </p>
            <div className="clima__agora">
              <p className="clima__ceu">{cartao.ceu}</p>
              <p className="clima__detalhe">
                Sensação {cartao.sensacao}° · Umidade {cartao.umidade}%
              </p>
            </div>
          </div>
          <ul className="clima__dias">
            {cartao.dias.map((dia) => (
              <li key={dia.nome} className="clima__dia">
                <span className="clima__dia-nome">{dia.nome}</span>
                <span className="clima__dia-faixa">
                  {dia.maxima}° <small>{dia.minima}°</small>
                </span>
                <span className="clima__dia-chuva">
                  chuva {dia.chuva === null ? "?" : `${dia.chuva}%`}
                </span>
              </li>
            ))}
          </ul>
        </>
      );
    case "lembretes":
      return (
        <ul className="cartao__lista">
          {cartao.itens.slice(0, 5).map((item, i) => (
            <li key={i} className="cartao__item">
              <span className="cartao__hora">{item.hora}</span>
              <span>{item.texto}</span>
            </li>
          ))}
        </ul>
      );
    case "pesquisa":
      return (
        <ul className="cartao__lista">
          {cartao.itens.map((item, i) => (
            <li key={i} className="achado">
              <p className="achado__titulo">{item.titulo}</p>
              {item.resumo && <p className="achado__resumo">{item.resumo}</p>}
              <p className="achado__fonte">{item.fonte}</p>
            </li>
          ))}
        </ul>
      );
    case "notas":
      return (
        <ul className="cartao__lista">
          {cartao.itens.map((nota, i) => (
            <li key={i} className="cartao__item">
              <span className="cartao__marca" aria-hidden="true" />
              <span>{nota}</span>
            </li>
          ))}
        </ul>
      );
    case "conta":
      return <p className="cartao__expressao">{cartao.expressao} =</p>;
    case "abrir":
      return null;
  }
}

/** O cartão pequeno da fileira: rótulo, título e o resumo de uma linha. */
export function CartaoMini({ cartao, numero }: { cartao: Cartao; numero: number }) {
  return (
    <article className="cartao-mini" title={`${cartao.rotulo}: ${cartao.titulo}`}>
      <span className="cartao-mini__rotulo">
        {String(numero).padStart(2, "0")} · {cartao.rotulo}
      </span>
      <span className="cartao-mini__resumo">{resumoDoCartao(cartao)}</span>
    </article>
  );
}

/** Enquanto a ferramenta roda: o que o Jarvis está fazendo, com uma barra correndo. */
export function CartaoProgresso({ ferramenta }: { ferramenta: string }) {
  return (
    <article className="cartao cartao--progresso" role="status">
      <span className="cartao__rotulo">Em andamento</span>
      <p className="cartao__titulo">{fraseDaFerramenta(ferramenta)}…</p>
      <span className="cartao__barra" aria-hidden="true" />
    </article>
  );
}
