# 🖥️ Frontend do Jarvis

O "rosto" do Jarvis: app de desktop feito com **Tauri 2 + React + TypeScript**
(decisão [0009](../docs/decisoes/0009-tauri-react-no-frontend.md)).

## Pré-requisitos (uma vez só)

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # Rust
# Node 20+ (já instalado)
```

## Comandos

```bash
npm install          # instala dependências
npm run tauri dev    # abre o app em modo desenvolvimento (recarrega ao salvar)
npm run build        # checa os tipos e gera o build da tela
npm test             # testes (Vitest)
```

## Estrutura

```
frontend/
├── src/            ← a tela (React + TypeScript)
├── src-tauri/      ← a "casca" nativa do app (Rust, quase não mexemos)
└── index.html
```

> A primeira execução do `tauri dev` compila o Rust e demora alguns minutos.
> Depois fica rápido.
