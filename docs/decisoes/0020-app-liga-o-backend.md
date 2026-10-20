# 0020 · O app liga o backend: um clique e tudo funciona

- **Status:** ✅ Aceita
- **Data:** 2026-10-20

## Contexto

Para usar o Jarvis era preciso abrir um terminal, ligar o backend e depois o
app. Reiniciou? Os lembretes sumiam. Um assistente que só funciona quando
alguém roda dois comandos não é usado no dia a dia.

## Decisão

**O app (Tauri) liga o backend ao abrir e o desliga ao fechar** (`src-tauri/src/backend.rs`).

- Se o backend já responde na porta 8765, o app só usa. Ao fechar, desliga
  apenas o que ELE ligou.
- Liga com o Python do ambiente do projeto (`backend/.venv`); sem ele, `uv run`.
  Um app aberto pelo Finder não herda o PATH do terminal, por isso o caminho é direto.
- A saída do servidor vai para `backend/dados/servidor.log`.
- Desliga com SIGTERM no Mac e no Linux (o servidor fecha direito) e encerra no Windows.
- Enquanto o backend carrega os modelos (~5 a 10 s), o app mostra "Iniciando o
  núcleo..." em vez de "desconectado".
- `JARVIS_BACKEND` aponta para outra pasta, se preciso.
- Junto: os **lembretes ficam em disco** (`dados/lembretes.json`) e voltam ao
  reiniciar. Os que venceram com o Jarvis desligado são avisados ao ligar.

## Alternativas consideradas

- **Empacotar o Python dentro do app (PyInstaller):** ~1 GB e frágil de montar
  nos três sistemas. Só vale se o Jarvis um dia for distribuído para outras pessoas.
- **Serviço do sistema sempre ligado** (launchd, systemd, Agendador do Windows):
  três configurações diferentes, contra a regra de concentrar as diferenças
  entre sistemas ([0012](0012-multiplataforma.md)).

## Consequências

- ✅ Um clique no app e tudo funciona, igual nos três sistemas
- ✅ Lembretes sobrevivem a reinícios
- ⚠️ A máquina precisa ter o projeto e o `uv sync` feito (é o caso das máquinas do dono)
- ⚠️ Com o app fechado, os lembretes não tocam: o próximo passo é o Jarvis
  ficar na barra de menus, com a janela fechada sem desligar nada
