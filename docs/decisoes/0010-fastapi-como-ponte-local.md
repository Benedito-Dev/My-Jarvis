# 0010 · FastAPI como ponte local entre backend e frontend

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

O frontend (Tauri + React, [0009](0009-tauri-react-no-frontend.md)) precisa
conversar com o backend Python, que é quem tem câmera, reconhecimento e voz.

## Decisão

O backend sobe uma **API HTTP local com FastAPI** (`jarvis servidor`):

- ouve **só em `127.0.0.1:8765`**, então nada fica exposto na rede;
- CORS liberado **apenas** para o app (`http://localhost:1420` em dev,
  `tauri://localhost` instalado);
- primeiro endereço: `GET /status` (nome, versão e habilidades).

O código fica em `backend/src/jarvis/api/`, separado das habilidades: a API é
uma **porta de entrada** que chama as habilidades, não uma habilidade.

## Alternativas consideradas

- **Comandos do Tauri (Rust) chamando o Python:** mais acoplado e exige escrever Rust.
- **Python como "sidecar" do Tauri:** bom para empacotar no futuro, mas ainda
  precisa de um protocolo. HTTP resolve isso e funciona com os dois rodando separados.
- **Flask:** funciona, mas o FastAPI já valida os tipos (Pydantic) e gera
  documentação automática em `/docs`.

## Consequências

- ✅ Frontend e backend independentes: cada um roda e é testado sozinho
- ✅ Documentação interativa grátis em `http://127.0.0.1:8765/docs`
- ⚠️ São dois processos para rodar (backend e app). Juntar os dois é assunto
  do Passo 4 (ligar tudo)
- ⚠️ Avisos em tempo real (ex.: "rosto reconhecido") vão pedir WebSocket mais adiante
