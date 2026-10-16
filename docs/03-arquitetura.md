# 🏗️ Arquitetura

## Visão geral: monorepo

Um único repositório com o **backend** e o **frontend** lado a lado.

```
My-Jarvis/
├── backend/     🧠 Python: o "cérebro" (câmera, reconhecimento, voz, IA)
├── frontend/    🖥️ a interface que o usuário vê (tecnologia a definir)
└── docs/        📚 documentação compartilhada
```

```
 frontend  ──── pede / mostra ────►  backend  ──►  📷 câmera, 🎤 microfone, 🤖 IA
 (tela)     ◄──── responde ───────   (lógica)
```

- O **backend** faz todo o trabalho pesado e não depende de interface.
- O **frontend** só mostra e envia comandos. Nunca acessa câmera nem decide nada.
- Enquanto o frontend não existir, o backend usa janelas simples do OpenCV para
  ver os resultados.

---

# Backend

## Decisão: organizar por **habilidade**, não por camada técnica

O Jarvis cresce ganhando habilidades (rosto, voz, IA...). Por isso cada
habilidade fica em **uma pasta só**, com tudo o que ela precisa.

```
❌ Por camada (MVC / controller-repository)     ✅ Por habilidade (feature)

controllers/                                   habilidades/
  face_controller.py                             desbloqueio_facial/
  voz_controller.py                                camera.py
services/                                          reconhecedor.py
  face_service.py                                  ...
  voz_service.py                                 voz/
repositories/                                      ...
  ...
→ uma habilidade espalhada em 3 pastas         → uma habilidade = uma pasta
```

**Por que não MVC ou controller/repository?** Esses padrões nasceram para
sistemas web com banco de dados. O Jarvis ainda não tem banco nem telas.
Criar essas camadas agora seria estrutura vazia.

## Estrutura de pastas do backend

```
backend/
├── src/
│   └── jarvis/
│       ├── __main__.py        ← ponto de entrada: `uv run python -m jarvis`
│       ├── nucleo/            ← coisas compartilhadas (caminhos, downloads)
│       └── habilidades/
│           └── desbloqueio_facial/
│               ├── fluxo.py         ← orquestra: liga entrada → lógica → saída
│               ├── camera.py        ← fala com o hardware
│               ├── reconhecedor.py  ← lógica pura (detecta e gera assinaturas)
│               ├── banco_rostos.py  ← salva/carrega as assinaturas em dados/
│               ├── tela.py          ← mostra o vídeo e as mensagens
│               └── modelos/         ← modelos de IA (os grandes são baixados, fora do git)
├── dados/                     ← rostos cadastrados (fora do git)
├── tests/
└── pyproject.toml
```

> A estrutura acima é o alvo. As pastas são criadas **só quando o passo precisar**.

## Dentro de cada habilidade: papéis

```
 camera.py  ──►  reconhecedor.py  ──►  tela.py
 (entrada)       (decide)              (saída)
                       │
                       ▼
                 banco_rostos.py
                 (guarda)
```

| Papel | Regra |
|---|---|
| Entrada (hardware) | Só captura dados. Não decide nada. |
| Lógica | Não sabe que existe câmera ou tela. Por isso é fácil de testar. |
| Saída (interface) | Só mostra. Não decide nada. |
| Persistência | Só salva e carrega arquivos em `dados/`. Não decide nada. |

O `fluxo.py` é o "maestro": chama cada papel na ordem certa, sem fazer o trabalho deles.

Separar a lógica do hardware permite testar o reconhecedor com uma foto,
sem precisar abrir a câmera.

## Convenções

- **Nomes em português** para pastas e módulos do domínio (`habilidades`, `reconhecedor`)
- Código Python segue o PEP 8 (o `ruff` garante)
- Dados pessoais (fotos, assinaturas faciais) **nunca** vão para o git

---

# Frontend

Ainda não definido (ver decisão [0005](decisoes/0005-monorepo-backend-frontend.md)).
A pasta `frontend/` existe para reservar o lugar.
