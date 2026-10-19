type Props = {
  versao: string;
  cadastrados: string[];
  onCadastrarRosto: () => void;
  onConfigurarPin: () => void;
};

export function PainelSistema({
  versao,
  cadastrados,
  onCadastrarRosto,
  onConfigurarPin,
}: Props) {
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
      <div className="painel__acoes">
        <button className="botao" type="button" onClick={onCadastrarRosto}>
          + Cadastrar rosto
        </button>
        <button className="botao botao--destaque" type="button" onClick={onConfigurarPin}>
          + Configurar acesso alternativo
        </button>
      </div>
    </section>
  );
}
