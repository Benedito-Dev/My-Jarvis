# My-Jarvis

Projeto pessoal em fase inicial. O escopo vai sendo definido ao longo dos commits.

## Estrutura

```
backend/    🧠 Python: o cérebro do Jarvis
frontend/   🖥️ interface (a definir)
docs/       📚 documentação
```

## Como rodar o backend

```bash
brew install uv cmake      # uma vez só
cd backend
uv sync                    # instala dependências
uv run python -m jarvis    # roda o Jarvis
uv run pytest              # testes
```

Documentação completa em [`docs/`](docs/README.md).
