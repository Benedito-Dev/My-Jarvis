import { useEffect, useState } from "react";

// Atualiza a cada segundo para o minuto virar na hora certa.
const INTERVALO_MS = 1000;

export function useRelogio(): Date {
  const [agora, setAgora] = useState(() => new Date());

  useEffect(() => {
    const intervalo = setInterval(() => setAgora(new Date()), INTERVALO_MS);
    return () => clearInterval(intervalo);
  }, []);

  return agora;
}
