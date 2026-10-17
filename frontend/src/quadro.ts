// Tamanho do quadro enviado ao backend: suficiente para reconhecer, leve para enviar.
export const LARGURA_QUADRO = 640;
const QUALIDADE_JPEG = 0.8;

/** Copia o quadro atual do vídeo (sem espelhar) para um JPEG reduzido. */
export function capturar(video: HTMLVideoElement, canvas: HTMLCanvasElement): Promise<Blob> {
  canvas.width = LARGURA_QUADRO;
  canvas.height = Math.round((LARGURA_QUADRO * video.videoHeight) / video.videoWidth);
  canvas.getContext("2d")!.drawImage(video, 0, 0, canvas.width, canvas.height);
  return new Promise((resolver, rejeitar) =>
    canvas.toBlob(
      (blob) => (blob ? resolver(blob) : rejeitar(new Error("Falha ao capturar o quadro"))),
      "image/jpeg",
      QUALIDADE_JPEG,
    ),
  );
}
