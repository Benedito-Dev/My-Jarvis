import { FormEvent, useState } from "react";
import { configurarPin } from "../api";

type Props = {
  usuario: string;
  onFechar: () => void;
  onConfigurado: () => void;
};

export function TelaCadastroPin({ usuario, onFechar, onConfigurado }: Props) {
  const [identificador, setIdentificador] = useState(usuario.toLowerCase());
  const [pin, setPin] = useState("");
  const [confirmacao, setConfirmacao] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [salvando, setSalvando] = useState(false);

  async function salvar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (pin.length !== 6 || pin !== confirmacao || identificador.trim().length < 3) return;

    setSalvando(true);
    setErro(null);
    try {
      await configurarPin(identificador, pin);
      onConfigurado();
    } catch (erroPin) {
      setErro(erroPin instanceof Error ? erroPin.message : "Não consegui configurar o PIN.");
    } finally {
      setSalvando(false);
    }
  }

  const pinDivergente = confirmacao.length > 0 && pin !== confirmacao;

  return (
    <div className="cadastro" role="dialog" aria-modal="true" aria-labelledby="pin-titulo">
      <div className="cadastro__caixa pin-config">
        <p className="pin-config__eyebrow">ACESSO ALTERNATIVO</p>
        <h2 id="pin-titulo">Configurar identificador e PIN</h2>
        <p className="pin-config__descricao">
          Este acesso funciona sem câmera. O identificador será digitado manualmente na tela de bloqueio;
          o Jarvis nunca exibirá uma lista de perfis.
        </p>

        <form className="pin-config__formulario" onSubmit={salvar}>
          <label className="cadastro__campo">
            Identificador
            <input
              className="cadastro__entrada"
              value={identificador}
              onChange={(evento) => setIdentificador(evento.target.value)}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              disabled={salvando}
              autoFocus
            />
          </label>

          <label className="cadastro__campo">
            PIN de 6 dígitos
            <input
              className="cadastro__entrada"
              value={pin}
              onChange={(evento) => setPin(evento.target.value.replace(/\D/g, "").slice(0, 6))}
              inputMode="numeric"
              type="password"
              maxLength={6}
              disabled={salvando}
            />
          </label>

          <label className="cadastro__campo">
            Confirmar PIN
            <input
              className="cadastro__entrada"
              value={confirmacao}
              onChange={(evento) => setConfirmacao(evento.target.value.replace(/\D/g, "").slice(0, 6))}
              inputMode="numeric"
              type="password"
              maxLength={6}
              disabled={salvando}
            />
          </label>

          {pinDivergente && <p className="pin-config__erro">Os PINs não conferem.</p>}
          {erro && <p className="pin-config__erro" role="alert">{erro}</p>}

          <div className="cadastro__acoes">
            <button className="botao" type="button" onClick={onFechar} disabled={salvando}>
              Cancelar
            </button>
            <button
              className="botao botao--destaque"
              type="submit"
              disabled={salvando || identificador.trim().length < 3 || pin.length !== 6 || pinDivergente}
            >
              {salvando ? "Salvando…" : "Salvar acesso"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
