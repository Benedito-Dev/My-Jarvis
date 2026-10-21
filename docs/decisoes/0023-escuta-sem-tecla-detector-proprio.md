# 0023 · Escuta sem tecla: detector de "Jarvis" treinado com a voz do dono + confirmação do Whisper

- **Status:** ✅ Aceita
- **Data:** 2026-10-21

## Contexto

Passo 5 da Fase 6: chamar o Jarvis pelo nome ("Jarvis, que horas são?") em vez
de segurar o ESPAÇO. Para isso o microfone fica aberto e algo precisa perceber
o nome: rápido, leve, local e sem disparar com a TV.

Medimos tudo com 40 gravações reais do dono (17 com "Jarvis") e falas sintéticas:

| Opção | Achou "Jarvis" | Alarmes falsos | Problema |
|---|---|---|---|
| openWakeWord pronto ("hey jarvis") | 1/17 | — | Treinado em inglês |
| Whisper ouvindo tudo | 23/29 | 3/47 | ~1,5 s de CPU por frase, o tempo todo |
| Detector treinado só com vozes sintéticas | 11/17 | ~12/hora | Não soa como o dono no microfone dele |
| **Detector treinado com a voz do dono** | **14/17** | **~3/hora** | Precisa das gravações do dono |

## Decisão

**Dois estágios, tudo local:**

1. **Detector pequeno** (`habilidades/escuta/detector.py`): os modelos genéricos
   do openWakeWord (espectrograma + embedding de fala do Google, Apache 2.0,
   baixados no primeiro uso) transformam o som em características, e uma rede
   pequena treinada com a voz do dono (`dados/escuta/jarvis.npz`, fora do git)
   decide. Dispara com duas notas seguidas acima de 0,7. Custa ~2% de um núcleo.
2. **Confirmação pelo Whisper**: o app grava o pedido (com 1,5 s de antes, onde
   está o "Jarvis") até a pessoa parar de falar e manda com `chamado=true`. Se a
   transcrição não tiver o nome, era alarme falso: o áudio é **apagado** e a tela
   nem muda.

- O app captura o som (como na [0013](0013-app-grava-o-audio.md)) e manda em
  16 kHz por um WebSocket (`/escuta`). A origem é conferida no backend (CORS não
  vale para WebSocket) e só funciona com a sessão aberta.
- Enquanto o Jarvis fala, pensa ou grava pelo ESPAÇO, a escuta não procura o
  nome (não acorda com a própria voz). O app também pede ao sistema o
  cancelamento de eco.
- "Jarvis" sozinho → "Pois não?", e o próximo pedido é gravado sem precisar do nome.
- Botão no rodapé liga e desliga a escuta (o microfone fecha de verdade).
- O ESPAÇO continua funcionando.

### Treinar e retreinar

`backend/ferramentas/treinar_escuta.py` refaz tudo: gera falas sintéticas (vozes
Piper e, no macOS, as do sistema), transcreve as gravações do dono
(`dados/gravacoes/`) para achar onde cada "Jarvis" termina e treina a rede. As
características são calculadas com os mesmos dois modelos ONNX do detector (sem
instalar o openWakeWord); só o treino precisa do `scikit-learn`, como extra:

    uv run --with scikit-learn python ferramentas/treinar_escuta.py [--avaliar]

Cada conversa vira gravação nova, então retreinar de tempos em tempos melhora o
detector. Na primeira rodada pelo projeto (47 gravações, 19 com o nome), o teste
honesto (metade treina, metade testa) achou **17 de 19**.

## Alternativas consideradas

- **Porcupine (Picovoice):** já tem "Jarvis" e costuma ser mais preciso, mas é
  código fechado e exige conta e chave conferida pela internet. Fica como plano B.
- **Treinar o modelo completo no próprio app:** precisa de ~400 MB de dados e
  ~15 min de treino; não cabe num cadastro.
- **Verificador pessoal leve sobre o detector genérico:** testado; o genérico
  barrava 7 dos 17 "Jarvis" do dono antes de o verificador ver.

## Consequências

- ✅ Chamar pelo nome, de longe do teclado, sem conta nem nuvem
- ✅ Alarme falso fica invisível (o Whisper descarta e o áudio é apagado)
- ⚠️ Perde ~1 em cada 10 chamadas nos testes: dá para repetir ou usar o ESPAÇO
- ⚠️ O detector é pessoal: outra pessoa (ou outra máquina) precisa treinar o seu
- ⚠️ Sem `dados/escuta/jarvis.npz` a escuta fica "indisponível" (o resto funciona)
