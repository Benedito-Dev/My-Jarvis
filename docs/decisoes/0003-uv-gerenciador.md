# 0003 · uv como gerenciador

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

Precisamos de ambiente virtual isolado e versões de dependências travadas.

## Decisão

Usar **uv** para ambiente, dependências e versão do Python.

## Alternativas consideradas

- **pip + venv:** vários comandos manuais e sem lockfile nativo.
- **Poetry:** funciona, mas é mais lento e mais pesado.

## Consequências

- ✅ Um comando só (`uv sync`), rápido, com versões travadas em `uv.lock`
- ⚠️ Precisa do `uv` instalado na máquina (`brew install uv`)
