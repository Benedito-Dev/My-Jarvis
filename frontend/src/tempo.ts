// Datas e horários sempre no fuso do Brasil, não no da máquina.
export const FUSO = "America/Sao_Paulo";

export function horaNoFuso(data: Date): number {
  const hora = new Intl.DateTimeFormat("pt-BR", {
    hour: "numeric",
    hourCycle: "h23",
    timeZone: FUSO,
  }).format(data);
  return Number(hora);
}

export function cumprimento(data: Date): string {
  const hora = horaNoFuso(data);
  if (hora >= 5 && hora < 12) return "Bom dia";
  if (hora >= 12 && hora < 18) return "Boa tarde";
  return "Boa noite";
}

export function formatarData(data: Date): string {
  return new Intl.DateTimeFormat("pt-BR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: FUSO,
  }).format(data);
}

export function formatarHora(data: Date): string {
  return new Intl.DateTimeFormat("pt-BR", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: FUSO,
  }).format(data);
}
