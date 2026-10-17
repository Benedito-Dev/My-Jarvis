# 🗺️ Roadmap

Legenda: ✅ feito · 🔄 em andamento · ⬜ pendente

## Fase 0: Fundação

| | Passo | Resultado visível |
|---|---|---|
| ✅ | Documentação base | Pasta `docs/` com visão, stack, arquitetura e roadmap |
| ✅ | Ambiente Python | `uv run python -m jarvis` imprime "Olá, eu sou o Jarvis" |
| ✅ | Monorepo | Pastas `backend/` e `frontend/` separadas |

## Fase 1: Desbloqueio facial

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Abrir a câmera | Seu vídeo aparece numa janela |
| ✅ | 2. Detectar rosto | Quadrado verde em volta do seu rosto |
| ✅ | 3. Cadastrar rosto | Seu rosto fica salvo em `dados/` |
| ✅ | 4. Reconhecer | "Bem-vindo, Benedito" ou "Acesso negado" |
| ✅ | 5. Bônus | "Por favor, aproxime seu rosto" + fala em voz alta |

## Fase 2: O rosto do Jarvis

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Nasce o frontend | Janela de app "J.A.R.V.I.S." abre (Tauri + React) |
| ✅ | 2. Backend vira servidor | O Python responde perguntas do frontend (FastAPI local) |
| ✅ | 3. Tela inicial | Saudação, data/hora e habilidades vindas do backend |
| ✅ | 4. Ligar tudo | Tela de bloqueio no app (câmera) → backend reconhece → tela inicial |
| ⬜ | 5. Botão Bloquear | Clicou → volta para a tela de bloqueio |

## Fase 2.5: Rodar nas três máquinas

[Decisão 0012](decisoes/0012-multiplataforma.md). O dono usa Linux, Windows e Mac.

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Voz por sistema | `motor_voz.py`: `say` no Mac, `spd-say` no Linux; testes passam nos 3 |
| ✅ | 2. App nativo no Linux | Janela do J.A.R.V.I.S. abre no Linux e desbloqueia pelo rosto |
| ⬜ | 3. App nativo no Windows | Motor de voz SAPI, origem CORS `http://tauri.localhost`, WebView2 |
| ⬜ | 4. Mesma voz nos 3 | Piper TTS local (pt-BR de verdade, não o espeak-ng robótico) |

## Fase 3: Conversa (planejada)

| | Passo | Resultado visível |
|---|---|---|
| ⬜ | 1. Ouvir | Segura ESPAÇO, fala, e o Jarvis grava a sua voz |
| ⬜ | 2. Transcrever | "Você disse: que horas são" (Whisper local) |
| ⬜ | 3. Comandos simples | "Que horas são?" → "São 16 e 30" |
| ⬜ | 4. Cérebro de IA | Pergunta livre → resposta (Claude) |
| ⬜ | 5. Bônus | Palavra de ativação "Jarvis" |

## Depois (ideias, sem ordem)

- 🖥️ Automações no Mac
- 🗣️ Voz mais natural (voz Premium do Mac ou voz de IA)
