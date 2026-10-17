# 0001 · Desktop, não web

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

O Jarvis precisa decidir onde roda: no navegador ou como aplicativo do computador.

## Decisão

Aplicativo de **desktop**, não página web.

> Esta decisão nasceu só para macOS (Apple Silicon). A
> [0012](0012-multiplataforma.md) ampliou o alvo para **macOS, Linux e
> Windows** — o que vale aqui é "desktop, não web".

## Alternativas consideradas

- **Aplicação web:** o navegador exige permissão a cada uso, só acessa a câmera
  com a aba aberta e bloqueia o acesso ao sistema (abrir apps, arquivos).

## Consequências

- ✅ Câmera e microfone contínuos, acesso ao sistema, roda em segundo plano
- ⚠️ Acesso pelo celular ou por outro lugar fica para depois, se um dia for necessário
