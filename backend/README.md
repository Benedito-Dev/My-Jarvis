# 🧠 Backend do Jarvis

O cérebro do Jarvis em Python 3.12. Arquitetura em [`docs/03-arquitetura.md`](../docs/03-arquitetura.md).

```bash
uv sync                    # instala dependências
uv run python -m jarvis cadastrar --nome SeuNome   # cadastra seu rosto (1ª vez)
uv run python -m jarvis                            # tela de bloqueio: desbloqueia pelo rosto
uv run python -m jarvis ver                        # só mostra a câmera com rostos marcados
uv run pytest              # testes
uv run ruff check .        # lint
```
