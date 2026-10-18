import type { Retangulo } from "../api";
import type { Tom } from "../desbloqueio";
import { contorno } from "../scanner";

// Altura da faixa que varre o rosto, em fração da altura do oval.
const FRACAO_DA_FAIXA = 0.18;

type Props = {
  rostos: Retangulo[];
  tom: Tom;
};

/**
 * Desenha a análise do rosto: um oval moldado na cabeça (girando junto com os
 * olhos) e uma faixa de luz que desce e sobe varrendo o rosto por dentro dele.
 */
export function Scanner({ rostos, tom }: Props) {
  return (
    <g className={`scanner scanner--${tom}`}>
      {rostos.map((rosto, indice) => (
        <RostoEscaneado key={indice} rosto={rosto} indice={indice} />
      ))}
    </g>
  );
}

function RostoEscaneado({ rosto, indice }: { rosto: Retangulo; indice: number }) {
  const { cx, cy, rx, ry, giro } = contorno(rosto);
  const faixa = Math.max(8, Math.round(ry * 2 * FRACAO_DA_FAIXA));

  // Ids únicos por rosto: dois rostos na tela não podem dividir o mesmo recorte.
  const recorte = `scanner-recorte-${indice}`;
  const brilho = `scanner-brilho-${indice}`;

  // Tudo gira junto com a cabeça, inclusive a direção da varredura.
  return (
    <g transform={`rotate(${giro} ${cx} ${cy})`}>
      <defs>
        {/* A luz só pode aparecer dentro do rosto. */}
        <clipPath id={recorte}>
          <ellipse cx={cx} cy={cy} rx={rx} ry={ry} />
        </clipPath>
        {/* Luz que some nas duas pontas, para parecer um feixe e não uma tarja. */}
        <linearGradient id={brilho} x1="0" y1="0" x2="0" y2="1">
          <stop className="scanner__luz scanner__luz--ponta" offset="0" />
          <stop className="scanner__luz scanner__luz--meio" offset="0.75" />
          <stop className="scanner__luz scanner__luz--ponta" offset="1" />
        </linearGradient>
      </defs>

      <ellipse className="scanner__halo" cx={cx} cy={cy} rx={rx} ry={ry} />
      <ellipse className="scanner__contorno" cx={cx} cy={cy} rx={rx} ry={ry} />

      {/* A varredura: a faixa de luz desce até o fim do rosto e volta subindo. */}
      <g clipPath={`url(#${recorte})`}>
        <g
          className="scanner__varredura"
          style={{ "--percurso": `${ry * 2 - faixa}px` } as React.CSSProperties}
        >
          <rect
            x={cx - rx}
            y={cy - ry}
            width={rx * 2}
            height={faixa}
            fill={`url(#${brilho})`}
          />
          <line
            className="scanner__feixe-halo"
            x1={cx - rx}
            x2={cx + rx}
            y1={cy - ry + faixa}
            y2={cy - ry + faixa}
          />
          <line
            className="scanner__feixe"
            x1={cx - rx}
            x2={cx + rx}
            y1={cy - ry + faixa}
            y2={cy - ry + faixa}
          />
        </g>
      </g>
    </g>
  );
}
