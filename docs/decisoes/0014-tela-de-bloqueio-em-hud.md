# 0014 · Tela de bloqueio em HUD: o rosto vai até o visor

- **Status:** ✅ Aceita
- **Data:** 2026-10-17

## Contexto

A tela de bloqueio desenhava um retângulo em volta do rosto, onde quer que ele
estivesse. Ao trocar o retângulo por um scanner (oval + varredura), ficou óbvio
um problema que o quadrado disfarçava: **o desenho chega atrasado**.

O desenho só se move quando o backend responde, e o ciclo é foto → JPEG → HTTP
→ YuNet → resposta → repintar. Medido nesta máquina (Linux, WebKitGTK):

| Etapa | Tempo |
|---|---|
| Backend decidir (`POST /desbloqueio/quadro`) | 12-18 ms |
| Tirar a foto e virar JPEG, câmera em 1280x720 | **101 ms** |
| Ciclo completo observado | ~1 quadro/s no pior caso |

Contra os 30 quadros/s do vídeo, qualquer movimento rápido deixa o desenho para
trás. Duas correções já entraram e ajudaram, mas não mudam a ordem de grandeza:
a câmera passou a ser pedida em 640x480 (a redução do quadro é feita na CPU) e
os `filter: drop-shadow` do SVG saíram — no WebKitGTK eles são desenhados na
CPU a cada quadro.

## Decisão

**Parar de perseguir o rosto e dar a ele um lugar fixo.** A tela de bloqueio
virou um HUD: a câmera aparece dentro de um **visor circular no centro**, e o
usuário posiciona o rosto ali. Com o rosto praticamente parado, o atraso do
acompanhamento deixa de ser percebido — e o scanner continua valendo.

Em volta do visor vêm os enfeites, todos em CSS/SVG:

```
Abertura.tsx     2,6 s de inicialização: eixos, log, molduras, íris abrindo
AneisHud.tsx     coroa de risquinhos e arcos girando; o progresso vira um arco
Scanner.tsx      o oval do rosto e a faixa de luz, só dentro do visor
LeiturasHud.tsx  colunas laterais: estado do sistema (real) e relógio
```

**O que é informação tem rótulo; o resto é declaradamente enfeite.** As barras
que pulsam no canto não medem nada e o código diz isso. Backend, câmera, rostos
na tela e progresso são valores de verdade.

## Alternativas consideradas

- **Detectar o rosto no próprio app, a 30 quadros/s** (MediaPipe em WASM), com o
  backend só decidindo quem é. Mataria o atraso de vez e daria 468 pontos — o
  contorno real do rosto, em vez do oval. Custa ~3 MB de modelo e um novo
  componente pesado no frontend. Continua sendo a saída se um dia quisermos
  acompanhamento de verdade; com o visor, deixou de ser necessário.
- **Suavizar o movimento no app** (interpolar entre as respostas): esconde o
  tremor, mas não tira a latência — em movimento rápido o atraso aparece igual.
- **Deixar como estava:** o próprio dono apontou que um atraso visível não passa
  impressão de qualidade, e a tela de bloqueio é a primeira coisa que se vê.

## Consequências

- ✅ O atraso do acompanhamento deixou de ser perceptível **sem** precisar de
  mais um modelo de visão no frontend
- ✅ A tela de bloqueio virou a vitrine do projeto, que é o que se espera de um
  "Jarvis"
- ✅ Só CSS e SVG: nenhuma dependência nova, e roda igual nos três sistemas
  ([0012](0012-multiplataforma.md))
- ✅ `prefers-reduced-motion` desliga a abertura e as animações
- ⚠️ **A câmera agora é pedida em 640x480.** A imagem do visor é um pouco menos
  nítida que antes, em troca de ~70 ms por quadro
- ⚠️ **O oval é uma aproximação.** O YuNet dá 5 pontos (olhos, nariz e cantos da
  boca): dá para posicionar, dimensionar e inclinar um oval, não para traçar o
  contorno do rosto
- ⚠️ As colunas laterais somem em janelas abaixo de 900 px, para não brigarem
  com o visor
