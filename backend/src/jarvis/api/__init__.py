"""API local: a ponte entre o backend e o frontend (só ouve em 127.0.0.1)."""

from jarvis.api.app import criar_app

__all__ = ["criar_app"]
