# 🧰 Stack

## Base

| Item | Escolha | Por quê |
|---|---|---|
| Plataforma | **Desktop: macOS, Linux e Windows** | Precisa de câmera, microfone e acesso ao sistema. As três máquinas do dono ([decisão 0012](decisoes/0012-multiplataforma.md)) |
| Repositório | **Monorepo** (`backend/` + `frontend/`) | Tudo versionado junto, cada lado com sua stack |
| Backend | **Python** | Melhor ecossistema para câmera, voz e IA |
| Versão | **Python 3.12** | Estável e compatível com as libs de visão (dlib, OpenCV). Versões mais novas ainda têm lacunas nessas libs |
| Gerenciador (backend) | **uv** | Cria o ambiente virtual, instala dependências e fixa versões (`uv.lock`) com um só comando |

## Frontend

| Item | Escolha |
|---|---|
| App de desktop | **Tauri 2** (casca nativa em Rust) |
| Tela | **React 19 + TypeScript**, com **Vite** |
| Pré-requisitos | Rust (rustup), Node 20+ / npm 11 |

Detalhes em [decisão 0009](decisoes/0009-tauri-react-no-frontend.md).

## Bibliotecas do backend (entram conforme o passo precisar)

| Lib | Para quê | Entra no passo |
|---|---|---|
| `opencv-python` | Abrir a câmera e desenhar na tela | 1 |
| `opencv-python` (YuNet) | Detectar rostos em tempo real ([decisão 0006](decisoes/0006-yunet-para-detectar-rostos.md)) | 2 |
| `opencv-python` (SFace) | Gerar a assinatura do rosto e comparar ([decisão 0007](decisoes/0007-sface-para-reconhecer-rostos.md)) | 3 e 4 |
| `say` (macOS) / `spd-say` (Linux) | O Jarvis falar em voz alta. Um motor por sistema, ambos embutidos ([decisões 0008](decisoes/0008-say-do-macos-para-falar.md) e [0012](decisoes/0012-multiplataforma.md)) | 5 |
| `fastapi` + `uvicorn` | API local para o frontend ([decisão 0010](decisoes/0010-fastapi-como-ponte-local.md)) | Fase 2 |

> Só adicionamos uma lib quando um passo do roadmap precisa dela.

### ⚠️ Armadilha conhecida: `face_recognition` (não usada, ver decisão 0007; fica de referência)

Testado em 2026-10-16 (Python 3.12, macOS Apple Silicon):

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
| `pytest` | Testes do backend |
| `vitest` | Testes do frontend |
| GitHub Actions | Roda os testes nos três sistemas a cada push ([decisão 0012](decisoes/0012-multiplataforma.md)) |

O CI está em `.github/workflows/testes.yml`. Ele roda `pytest`, `ruff`,
`vitest` e o `build` no Ubuntu, no macOS e no Windows — as três máquinas do
alvo. Não compila o app do Tauri: isso é lento e exige as libs nativas de cada
sistema, e o que costuma quebrar entre sistemas é o código, não o build.

## Pré-requisitos na máquina

O `uv` baixa o próprio Python 3.12, então basta instalar o `uv` e, para o app
do Tauri, o Rust e as libs de interface do sistema.

### macOS

```bash
brew install uv
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # Rust, para o Tauri
```

Se um dia o `dlib` voltar à mesa, ele precisa de `brew install cmake`.

### Linux (Debian/Ubuntu/Mint)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh                  # uv
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh   # Rust, para o Tauri

# Libs de interface que o Tauri compila contra (WebKitGTK)
sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev librsvg2-dev \
                 libayatana-appindicator3-dev libxdo-dev
```

A voz usa o `spd-say` (pacote `speech-dispatcher`), que já vem na maioria das
distros. Sem ele o Jarvis funciona, mas em silêncio.

### Windows

Ainda não verificado — ver [decisão 0012](decisoes/0012-multiplataforma.md).
Vai precisar do `uv`, do Rust (MSVC) e do WebView2.

> Verificado em 2026-10-16: macOS (Apple Silicon) e Linux Mint 21.3.
