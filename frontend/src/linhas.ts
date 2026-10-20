/**
 * Junta os pedaços que chegam pela rede em linhas completas. Um pedaço pode
 * terminar no meio de uma linha (ou trazer várias): o que sobra fica guardado
 * até o próximo. Serve para ler o fluxo NDJSON da conversa.
 */
export class LeitorDeLinhas {
  private resto = "";

  empurrar(pedaco: string): string[] {
    const partes = (this.resto + pedaco).split("\n");
    this.resto = partes.pop() ?? "";
    return partes.filter((linha) => linha.trim() !== "");
  }

  /** O que sobrou sem "\n" no fim do fluxo. */
  terminar(): string[] {
    const ultima = this.resto.trim();
    this.resto = "";
    return ultima ? [ultima] : [];
  }
}
