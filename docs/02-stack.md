# 🧰 Stack

## Base

| Item | Escolha | Por quê |
|---|---|---|
| Plataforma | **Desktop (macOS, Apple Silicon)** | Precisa de câmera, microfone e acesso ao sistema |
| Repositório | **Monorepo** (`backend/` + `frontend/`) | Tudo versionado junto, cada lado com sua stack |
| Backend | **Python** | Melhor ecossistema para câmera, voz e IA |
| Versão | **Python 3.12** | Estável e compatível com as libs de visão (dlib, OpenCV). Versões mais novas ainda têm lacunas nessas libs |
| Gerenciador (backend) | **uv** | Cria o ambiente virtual, instala dependências e fixa versões (`uv.lock`) com um só comando |

## Frontend

📋 **A definir.** Será decidido quando a primeira tela for necessária.

## Bibliotecas do backend (entram conforme o passo precisar)

| Lib | Para quê | Entra no passo |
|---|---|---|
| `opencv-python` | Abrir a câmera e desenhar na tela | 1 |
| `face_recognition` | Detectar e comparar rostos (usa dlib por baixo) | 2 a 4 |

> Só adicionamos uma lib quando um passo do roadmap precisa dela.

### ⚠️ Armadilha conhecida: `face_recognition`

Testado em 2026-10-16 (Python 3.12, Apple Silicon):

| Sintoma | Causa | Correção |
|---|---|---|
| `No module named 'pkg_resources'` ao importar | A lib está sem manutenção desde 2020 e usa `pkg_resources`, removido no `setuptools` 81 | Adicionar `setuptools<81` às dependências junto com a lib |
| Instalação demora ~12 min | O `dlib` é compilado do zero (precisa de `cmake`) | Normal, só na primeira vez (depois fica em cache) |

```bash
uv add face_recognition "setuptools<81"
```

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
