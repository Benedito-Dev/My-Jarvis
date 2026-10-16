# My-Jarvis

Projeto pessoal em fase inicial. O escopo vai sendo definido ao longo dos commits.

## Estrutura

```
backend/    🧠 Python: o cérebro do Jarvis
frontend/   🖥️ Tauri + React: o rosto do Jarvis
docs/       📚 documentação
```

## Como rodar o backend

```bash
brew install uv cmake      # uma vez só
cd backend
uv sync                    # instala dependências
uv run python -m jarvis cadastrar --nome SeuNome   # cadastra seu rosto (1ª vez)
uv run python -m jarvis                            # tela de bloqueio: desbloqueia pelo rosto
uv run python -m jarvis ver                        # só mostra a câmera com rostos marcados
uv run pytest              # testes
```

Documentação completa em [`docs/`](docs/README.md).

## Como rodar o frontend

```bash
cd frontend
npm install                # (no Node 20, use: npx npm@11 install)
npm run tauri dev          # abre o app
```
