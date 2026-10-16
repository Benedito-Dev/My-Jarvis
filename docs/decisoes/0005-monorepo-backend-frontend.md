# 0005 · Monorepo com backend e frontend

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

O Jarvis vai ter uma parte que pensa (câmera, reconhecimento, voz, IA) e uma
parte que o usuário vê (interface). As duas podem usar tecnologias diferentes.

## Decisão

**Monorepo**: um único repositório com `backend/` e `frontend/` na raiz,
e `docs/` compartilhado.

- `backend/`: Python 3.12 + uv (decisões [0002](0002-python-3-12.md) e [0003](0003-uv-gerenciador.md))
- `frontend/`: tecnologia **a definir** quando a primeira tela for necessária

## Alternativas consideradas

- **Projeto único sem separação:** mistura interface e lógica, o que dificulta
  trocar a interface no futuro.
- **Dois repositórios:** mais trabalho para manter sincronizados e versionar
  juntos. Exagero para um projeto pessoal.

## Consequências

- ✅ Backend e frontend evoluem juntos, no mesmo commit quando preciso
- ✅ Cada lado pode ter sua própria stack e suas ferramentas
- ⚠️ Precisaremos definir como os dois conversam (ex.: HTTP/WebSocket local)
  quando o frontend nascer, numa decisão própria
