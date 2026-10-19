// Prepara o que o MediaPipe precisa para rodar no app (decisão 0015):
// - copia o runtime WASM do node_modules para public/visao/wasm
// - baixa o modelo de malha do rosto (~3,6 MB), só se ainda não estiver lá
// Nada disso vai para o git: é refeito a cada `npm run dev` / `npm run build`.
import { copyFile, mkdir, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), "..");
const DESTINO = join(RAIZ, "public", "visao");
const ORIGEM_WASM = join(RAIZ, "node_modules", "@mediapipe", "tasks-vision", "wasm");
const MODELO = join(DESTINO, "face_landmarker.task");
const URL_MODELO =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

async function existe(caminho) {
  try {
    return (await stat(caminho)).size > 0;
  } catch {
    return false;
  }
}

await mkdir(join(DESTINO, "wasm"), { recursive: true });
for (const arquivo of await readdir(ORIGEM_WASM)) {
  await copyFile(join(ORIGEM_WASM, arquivo), join(DESTINO, "wasm", arquivo));
}

if (!(await existe(MODELO))) {
  console.log("Baixando o modelo de malha do rosto...");
  const resposta = await fetch(URL_MODELO);
  if (!resposta.ok) throw new Error(`Falha ao baixar o modelo: HTTP ${resposta.status}`);
  await writeFile(MODELO, Buffer.from(await resposta.arrayBuffer()));
}
