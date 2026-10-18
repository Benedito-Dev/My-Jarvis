// Tudo aqui é enfeite: anéis, arcos e marcações girando em volta do visor.
// Desenhado num quadrado 200x200 e esticado pelo CSS, então nada depende do
// tamanho real da tela.

const CENTRO = 100;

// Risquinhos da borda externa: 60 traços, um a cada 6 graus.
const RISCOS = Array.from({ length: 60 }, (_, i) => i * 6);

type Props = {
  /** 0 a 1: quanto do reconhecimento já foi confirmado. */
  progresso: number;
};

export function AneisHud({ progresso }: Props) {
  const raioProgresso = 92;
  const voltaProgresso = 2 * Math.PI * raioProgresso;

  return (
    <svg className="aneis" viewBox="0 0 200 200" aria-hidden="true">
      {/* Anel externo fixo, de referência */}
      <circle className="aneis__borda" cx={CENTRO} cy={CENTRO} r={98} />

      {/* Coroa de risquinhos, girando devagar */}
      <g className="aneis__coroa">
        {RISCOS.map((grau) => (
          <line
            key={grau}
            className={grau % 30 === 0 ? "aneis__risco aneis__risco--longo" : "aneis__risco"}
            x1={CENTRO}
            y1={6}
            x2={CENTRO}
            y2={grau % 30 === 0 ? 16 : 11}
            transform={`rotate(${grau} ${CENTRO} ${CENTRO})`}
          />
        ))}
      </g>

      {/* Dois arcos girando em sentidos opostos */}
      <circle className="aneis__arco aneis__arco--horario" cx={CENTRO} cy={CENTRO} r={88} />
      <circle className="aneis__arco aneis__arco--anti" cx={CENTRO} cy={CENTRO} r={80} />

      {/* O progresso do reconhecimento vira um arco que fecha em volta do rosto */}
      <circle
        className="aneis__progresso"
        cx={CENTRO}
        cy={CENTRO}
        r={raioProgresso}
        strokeDasharray={voltaProgresso}
        strokeDashoffset={voltaProgresso * (1 - progresso)}
        transform={`rotate(-90 ${CENTRO} ${CENTRO})`}
      />
    </svg>
  );
}
