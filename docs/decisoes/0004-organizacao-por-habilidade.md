# 0004 · Organização por habilidade

- **Status:** ✅ Aceita
- **Data:** 2026-10-16

## Contexto

Precisamos definir como organizar pastas e camadas do código. O Jarvis vai
crescer ganhando habilidades (rosto, voz, IA...).

## Decisão

Cada habilidade em **sua própria pasta** (`src/jarvis/habilidades/<nome>/`),
com separação interna entre entrada, lógica e saída.
Detalhes em [03-arquitetura.md](../03-arquitetura.md).

## Alternativas consideradas

- **MVC:** pensado para apps web com telas e banco. Espalharia uma habilidade em 3 pastas.
- **controller/service/repository:** não há banco nem API. As camadas seriam estrutura vazia.

## Consequências

- ✅ Nova habilidade = nova pasta, sem mexer nas outras
- ✅ Lógica separada do hardware, então dá pra testar sem câmera
- ⚠️ Código compartilhado precisa ir para `nucleo/`, para não duplicar entre habilidades
