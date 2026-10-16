# 0009 · Tauri + React + TypeScript no frontend

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

Com o desbloqueio facial pronto, o Jarvis precisa de uma "casa": uma tela
inicial para onde o usuário vai depois de desbloquear. É a hora de a pasta
`frontend/` (reservada na [0005](0005-monorepo-backend-frontend.md)) ganhar vida.

## Decisão

**Tauri 2 + React + TypeScript**, com Vite.

- A tela é feita em React/TypeScript (`frontend/src/`)
- O Tauri é a "casca" nativa do app (`frontend/src-tauri/`, em Rust, quase não mexemos)
- O backend Python vai virar um **servidor local** (FastAPI) com que o frontend
  conversa. Isso fica numa decisão própria no Passo 2.

## Alternativas consideradas

- **Electron + React:** o mais popular, mas pesado (~150 MB por app).
- **pywebview + React:** o Python abriria a janela. Simples, mas com poucos recursos
  de app nativo.
- **Interface em Python (PySide/Qt):** dispensaria o frontend separado, mas fugiria
  do monorepo e do TypeScript que o Benedito já usa.

## Consequências

- ✅ App nativo e leve (~10 MB), com caminho aberto para ícone na barra de menu e
  atalhos globais (ex.: "Ei Jarvis")
- ✅ TypeScript/React, stack que o Benedito já conhece
- ⚠️ Precisa do Rust instalado (rustup) e a primeira compilação leva ~1 min
- ⚠️ O npm do Node 20 tem um bug de instalação (`edgesOut`). Use `npx npm@11 install`
  ou atualize o Node para 22+
