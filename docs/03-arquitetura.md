# 🏗️ Arquitetura

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

## Estrutura de pastas

```
My-Jarvis/
├── docs/                      ← você está aqui
├── src/
│   └── jarvis/
│       ├── __main__.py        ← ponto de entrada: `uv run python -m jarvis`
│       ├── nucleo/            ← coisas compartilhadas (config, log)
│       └── habilidades/
│           └── desbloqueio_facial/
│               ├── camera.py        ← fala com o hardware
│               ├── reconhecedor.py  ← lógica pura (compara rostos)
│               └── tela.py          ← mostra o vídeo e as mensagens
├── dados/                     ← rostos cadastrados (fora do git)
├── tests/
└── pyproject.toml
```

> A estrutura acima é o alvo. As pastas são criadas **só quando o passo precisar**.

## Dentro de cada habilidade: 3 papéis

```
 camera.py  ──►  reconhecedor.py  ──►  tela.py
 (entrada)       (decide)              (saída)
```

| Papel | Regra |
|---|---|
| Entrada (hardware) | Só captura dados. Não decide nada. |
| Lógica | Não sabe que existe câmera ou tela. Por isso é fácil de testar. |
| Saída (interface) | Só mostra. Não decide nada. |

Separar a lógica do hardware permite testar o reconhecedor com uma foto,
sem precisar abrir a câmera.

## Convenções

- **Nomes em português** para pastas e módulos do domínio (`habilidades`, `reconhecedor`)
- Código Python segue o PEP 8 (o `ruff` garante)
- Dados pessoais (fotos, assinaturas faciais) **nunca** vão para o git
