# 🧰 Stack

## Base

| Item | Escolha | Por quê |
|---|---|---|
| Plataforma | **Desktop (macOS, Apple Silicon)** | Precisa de câmera, microfone e acesso ao sistema |
| Linguagem | **Python** | Melhor ecossistema para câmera, voz e IA |
| Versão | **Python 3.12** | Estável e compatível com as libs de visão (dlib, OpenCV). Versões mais novas ainda têm lacunas nessas libs |
| Gerenciador | **uv** | Cria o ambiente virtual, instala dependências e fixa versões (`uv.lock`) com um só comando |

## Bibliotecas (entram conforme o passo precisar)

| Lib | Para quê | Entra no passo |
|---|---|---|
| `opencv-python` | Abrir a câmera e desenhar na tela | 1 |
| `face_recognition` | Detectar e comparar rostos (usa dlib por baixo) | 2 a 4 |

> Só adicionamos uma lib quando um passo do roadmap precisa dela.

## Ferramentas de qualidade

| Ferramenta | Para quê |
|---|---|
| `ruff` | Lint e formatação (um só comando) |
| `pytest` | Testes |

## Pré-requisitos na máquina

```bash
brew install uv cmake   # cmake é necessário para compilar o dlib
```

O Python 3.12 já está instalado via Homebrew (`/opt/homebrew/bin/python3.12`).
O `uv` também consegue baixar o Python sozinho, se precisar.
