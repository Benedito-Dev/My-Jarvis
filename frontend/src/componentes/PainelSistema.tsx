type Props = {
  versao: string;
  cadastrados: string[];
  onCadastrarRosto: () => void;
};

export function PainelSistema({ versao, cadastrados, onCadastrarRosto }: Props) {
  return (
    <section className="painel">
      <h2 className="painel__titulo">Sistema</h2>
      <dl className="dados">
        <dt>Rostos cadastrados</dt>
        <dd>
          {cadastrados.length === 0
            ? "Nenhum"
            : `${cadastrados.length} (${cadastrados.join(", ")})`}
        </dd>
        <dt>Versão</dt>
        <dd>{versao}</dd>
      </dl>
      <button className="botao" type="button" onClick={onCadastrarRosto}>
        + Cadastrar rosto
      </button>
    </section>
  );
}
