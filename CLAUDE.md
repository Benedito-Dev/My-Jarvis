# My-Jarvis: instruções para o Claude

Assistente pessoal de desktop em **monorepo**: `backend/` (Python 3.12 + uv),
`frontend/` (Tauri 2 + React + TypeScript) e `docs/`.

Roda em **macOS, Linux e Windows** (decisão `0012`). Diferença entre sistemas
fica concentrada num arquivo só (ex.: `nucleo/motor_voz.py`), nunca espalhada em
`if sys.platform` — e os testes precisam passar nas três máquinas. O CI
(`.github/workflows/testes.yml`) confere isso a cada push.

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
- O dono do projeto é o **Benedito**
- Nome do assistente é configuração (`nucleo/config.py`, env `JARVIS_NOME`), não constante:
  o frontend exibe o que vier de `/status`

## Comandos (dentro de `backend/`)

```bash
uv sync                    # instala dependências (o app usa o .venv criado aqui)
uv run python -m jarvis servidor   # liga só o backend (o app já faz isso sozinho)
uv run python -m jarvis    # desbloqueio pelo terminal (sem o app)
uv run pytest              # testes
uv run ruff check . && uv run ruff format --check .
```

## Comandos (dentro de `frontend/`)

```bash
npx npm@11 install         # o npm do Node 20 tem bug (edgesOut)
npm run build              # tsc + vite build (checa os tipos)
npm test                   # testes (Vitest)
npm run tauri dev          # abre o app
```
