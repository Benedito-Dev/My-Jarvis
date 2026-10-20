# 🗺️ Roadmap

Legenda: ✅ feito · 🔄 em andamento · ⬜ pendente

## Fase 0: Fundação

| | Passo | Resultado visível |
|---|---|---|
| ✅ | Documentação base | Pasta `docs/` com visão, stack, arquitetura e roadmap |
| ✅ | Ambiente Python | `uv run python -m jarvis` imprime "Olá, eu sou o Jarvis" |
| ✅ | Monorepo | Pastas `backend/` e `frontend/` separadas |

## Fase 1: Desbloqueio facial

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Abrir a câmera | Seu vídeo aparece numa janela |
| ✅ | 2. Detectar rosto | Quadrado verde em volta do seu rosto |
| ✅ | 3. Cadastrar rosto | Seu rosto fica salvo em `dados/` |
| ✅ | 4. Reconhecer | "Bem-vindo, Benedito" ou "Acesso negado" |
| ✅ | 5. Bônus | "Por favor, aproxime seu rosto" + fala em voz alta |

## Fase 2: O rosto do Jarvis

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Nasce o frontend | Janela de app "J.A.R.V.I.S." abre (Tauri + React) |
| ✅ | 2. Backend vira servidor | O Python responde perguntas do frontend (FastAPI local) |
| ✅ | 3. Tela inicial | Saudação, data/hora e habilidades vindas do backend |
| ✅ | 4. Ligar tudo | Tela de bloqueio no app (câmera) → backend reconhece → tela inicial |
| ✅ | 5. Botão Bloquear | Clicou → volta para a tela de bloqueio |
| ✅ | 6. Cadastrar pelo app | "+ Cadastrar rosto" captura 5 amostras, sem terminal |
| ✅ | 7. Tela de bloqueio em HUD | Abertura animada, visor circular central e scanner no rosto ([decisão 0014](decisoes/0014-tela-de-bloqueio-em-hud.md)) |
| ✅ | 8. Desbloqueio fluido | Malha 3D do rosto em tempo real no app; o visor se abre como um portal para o painel ([decisão 0015](decisoes/0015-malha-do-rosto-no-app.md)) |
| ✅ | 9. Central de comando | Núcleo de partículas no centro que pulsa com a voz real; sistema, relógio e habilidades nas laterais |

## Fase 2.5: Rodar nas três máquinas

[Decisão 0012](decisoes/0012-multiplataforma.md). O dono usa Linux, Windows e Mac.

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Voz por sistema | `motor_voz.py`: `say` no Mac, `spd-say` no Linux; testes passam nos 3 |
| ✅ | 2. App nativo no Linux | Janela do J.A.R.V.I.S. abre no Linux e desbloqueia pelo rosto |
| ⬜ | 3. App nativo no Windows | Motor de voz SAPI e WebView2 (a origem CORS do Windows já está liberada) |
| ✅ | 4. Mesma voz nos 3 | Piper TTS local com a voz "Faber", escolhida de ouvido ([decisão 0017](decisoes/0017-voz-piper-faber.md)) |

## Fase 3: Conversa

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Ouvir | Segura ESPAÇO, fala, e o Jarvis grava a sua voz; o núcleo pulsa com o volume |
| ✅ | 2. Transcrever | "Você disse: que horas são" (Whisper local, [decisão 0016](decisoes/0016-whisper-local-para-transcrever.md)) |
| ✅ | 3. Comandos simples | "Que horas são?" → "São 14 horas e 3."; também data e "bloquear", e o núcleo "fala" junto |
| ✅ | 4. Cérebro de IA | Pergunta livre → resposta falada (DeepSeek pelo OpenRouter, [decisão 0018](decisoes/0018-cerebro-openrouter-deepseek.md)) |
| ⬜ | 5. Bônus | Palavra de ativação "Jarvis" |

## Fase 4: Autonomia (memória e mãos)

[Decisão 0019](decisoes/0019-ferramentas-da-ia.md). Do assistente que conversa para o que **age**.

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Memória curta | "Que dia é hoje?" → "E amanhã?" entende o "amanhã" |
| ✅ | 2. Primeira mão: lembretes | "Me lembra de X daqui a 20 min" → ele avisa em voz; módulo 04 no painel |
| ✅ | 3. Pesquisar na web | "Como foi o jogo do Flamengo ontem?" (DuckDuckGo, grátis) |
| ✅ | 4. Abrir apps e sites | "Abre o Spotify", "Abre o YouTube com lofi" |
| ✅ | 5. Clima, notas e calculadora | "Vai chover amanhã?", "Anota: comprar café", "17% de 3480" |
| ⬜ | 6. Controlar o sistema | "Abaixa o volume", "Como tá a bateria?" |
| ⬜ | 7. Memória longa | Lembra de fatos sobre o dono entre os dias |

## Fase 5: Uso no dia a dia

[Decisão 0020](decisoes/0020-app-liga-o-backend.md). O Jarvis pronto para ser usado todo dia, sem terminal.

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Lembretes em disco | Reiniciou? Os lembretes voltam, e os vencidos são avisados ao ligar |
| ✅ | 2. Um clique liga tudo | Abrir o app sobe o backend; fechar desliga ("Iniciando o núcleo..." enquanto carrega) |
| ⬜ | 3. Jarvis.app instalado | Ícone em Aplicativos e no Dock, abre ao ligar o computador |
| ⬜ | 4. Barra de menus | Fechar a janela não desliga o Jarvis: lembretes tocam com ela fechada |

## Fase 6: "Jarvis, bom dia"

O destino: você diz **"Jarvis, bom dia"** e ele conta o seu dia **falando e
mostrando cartões na tela**. A tela deixa de ser um dashboard e vira a conversa.

| | Passo | Resultado visível |
|---|---|---|
| ✅ | 1. Orbe de fios de luz | O núcleo vira um anel de laços de luz que se agita com a voz |
| ✅ | 2. Tela limpa | Manchete de estado (EM ESPERA, FALANDO...), legenda da fala e módulos pequenos nos cantos |
| ✅ | 3. Cartões | "Como está o clima?" → um cartão de clima na frente do orbe; também lembrete, nota e pesquisa |
| ⬜ | 4. Bom dia | "Bom dia" → clima + lembretes de hoje + notícias, um cartão por assunto |
| ⬜ | 5. Sem tecla | Palavra de ativação "Jarvis" (o bônus da Fase 3) |
| ⬜ | 6. Sua agenda e e-mail | Google Agenda e Gmail entram no bom dia |

## Depois (ideias, sem ordem)

- 🖥️ Automações no Mac
