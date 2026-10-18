// A sequência de abertura da tela de bloqueio: eixos cortando a tela, o log de
// inicialização aparecendo linha a linha e as molduras dos cantos. Depois disso
// o visor abre. É só enfeite — nada aqui decide nada.

/** Quanto tempo a abertura inteira dura, do primeiro risco ao visor aberto. */
export const DURACAO_ABERTURA_MS = 2600;

const LINHAS = [
  "INICIANDO NÚCLEO",
  "MÓDULO DE VISÃO ................ OK",
  "RECONHECIMENTO FACIAL .......... OK",
  "CÂMERA ......................... ONLINE",
  "AGUARDANDO OPERADOR",
];

// Quando cada linha do log entra, em segundos.
const PRIMEIRA_LINHA_S = 0.35;
const ENTRE_LINHAS_S = 0.22;

export function Abertura({ nomeAssistente }: { nomeAssistente: string }) {
  return (
    <div className="abertura" aria-hidden="true">
      <div className="abertura__eixo abertura__eixo--horizontal" />
      <div className="abertura__eixo abertura__eixo--vertical" />

      {["ne", "no", "se", "so"].map((canto) => (
        <span key={canto} className={`abertura__moldura abertura__moldura--${canto}`} />
      ))}

      <p className="abertura__marca">{nomeAssistente}</p>

      <ul className="abertura__log">
        {LINHAS.map((linha, indice) => (
          <li
            key={linha}
            style={{ animationDelay: `${PRIMEIRA_LINHA_S + indice * ENTRE_LINHAS_S}s` }}
          >
            {linha}
          </li>
        ))}
      </ul>
    </div>
  );
}
