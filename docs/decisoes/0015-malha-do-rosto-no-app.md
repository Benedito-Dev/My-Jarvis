# 0015 · Malha do rosto no app (MediaPipe), o backend continua decidindo

- **Status:** ✅ Aceita
- **Data:** 2026-10-19

## Contexto

A [0014](0014-tela-de-bloqueio-em-hud.md) fixou o rosto no visor para esconder o
atraso do desenho, que só se mexia quando o backend respondia. Não bastou: no
Mac, o dono achou a tela travada, pouco fluida e pouco "Jarvis". O oval tem um
limite que nenhum ajuste de CSS resolve: depende da ida e volta ao backend e só
tem 5 pontos.

Medido no Mac (2026-10-19): o backend leva ~6 ms por quadro e o app manda ~20
quadros/s. O problema não era velocidade: o desenho estava preso ao backend, e
o desbloqueio confirmava em 0,25 s, durante a abertura, antes de o rosto aparecer.

## Decisão

**O app roda o MediaPipe Face Landmarker sobre o vídeo, a cada quadro, e
desenha uma malha de 478 pontos colada no rosto.** O backend continua sendo o
único que decide **quem** é ([0011](0011-app-captura-backend-decide.md)): a
malha é só o que a pessoa vê.

Junto com isso:

- o reconhecimento só começa depois da abertura animada;
- confirmar exige a mesma pessoa por **1,2 s** (além de 5 quadros), para o
  scanner ser visto trabalhando em qualquer máquina, rápida ou lenta;
- os modelos do backend são carregados uma vez só, e não a cada bloqueio (2 s).

O runtime WASM e o modelo (~3,6 MB) não vão para o git:
`frontend/scripts/preparar-visao.mjs` copia e baixa tudo antes de `dev`/`build`.

## Alternativas consideradas

- **Continuar só com o oval da 0014:** foi o que o dono rejeitou.
- **Pedir os 478 pontos ao backend:** volta a prender o desenho na ida e volta HTTP.
- **Mover o reconhecimento inteiro para o app:** tiraria a decisão do backend,
  contra a 0011.

## Consequências

- ✅ O desenho acompanha o rosto na velocidade da câmera, sem esperar o backend
- ✅ Malha, íris e contornos de verdade, em vez de um oval aproximado
- ✅ Funciona igual nos três sistemas: é WASM + WebGL no WebView ([0012](0012-multiplataforma.md)),
  com volta para CPU quando não houver GPU
- ⚠️ Mais ~400 KB de JS no app e ~3,6 MB de modelo baixados no primeiro `npm run dev`
- ⚠️ Dois detectores de rosto rodando (MediaPipe no app, YuNet no backend).
  Eles podem discordar por um quadro; quem vale é o backend
- ⚠️ Falta medir no Linux (WebKitGTK) se a GPU funciona ou se cai para CPU
