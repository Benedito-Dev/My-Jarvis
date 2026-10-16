# My-Jarvis: instruções para o Claude

Assistente pessoal de desktop (macOS) em **monorepo**: `backend/` (Python 3.12 + uv),
`frontend/` (a definir) e `docs/`.

## 📚 Fonte da verdade

Antes de propor algo, leia `docs/`, principalmente `03-arquitetura.md`,
`04-roadmap.md` e `decisoes/`. Decisão nova = novo arquivo em `docs/decisoes/`
(copie o `_modelo.md`). Passo concluído = marcar no roadmap.

## ⚠️ Regras herdadas da pasta pai

Este projeto fica dentro de `Benedito/`, cujas regras em `Benedito/.claude/rules/`
são do **Devari Core** (TypeScript/NestJS). Neste projeto:

| Regra | Vale aqui? |
|---|---|
| `devari-conventional-commits.md` (commits em português, com scope) | ✅ Sim |
| `devari-backend-patterns.md`, `devari-3-pilares.md`, `devari-event-naming.md`, `devari-jsdoc-templates.md`, `devari-migration-protocol.md` | ❌ Não. Prisma, NestJS, DClasse, BigInt etc. não existem aqui |

Scopes de commit deste projeto: `docs`, `backend`, `frontend`, `core`, ou o nome
da habilidade (ex.: `desbloqueio-facial`).

## Como trabalhar

- **Passos pequenos que terminam**: cada passo precisa funcionar e ser visível
- Organização por **habilidade** (`backend/src/jarvis/habilidades/<nome>/`), não MVC
- Só adicione lib ou pasta quando o passo atual precisar
- Dados pessoais (`dados/`) nunca vão para o git

## Comandos (dentro de `backend/`)

```bash
uv sync                    # instala dependências
uv run python -m jarvis    # roda
uv run pytest              # testes
uv run ruff check . && uv run ruff format --check .
```
