import { cumprimento, formatarData, formatarHora } from "../tempo";

type Props = {
  agora: Date;
  nome: string | null;
};

export function Saudacao({ agora, nome }: Props) {
  return (
    <section className="saudacao">
      <h1 className="saudacao__titulo">
        {cumprimento(agora)}
        {nome && <span className="saudacao__nome">, {nome}</span>}.
      </h1>
      <p className="saudacao__data">{formatarData(agora)}</p>
      <p className="saudacao__hora">{formatarHora(agora)}</p>
    </section>
  );
}
