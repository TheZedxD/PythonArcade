"""Matrix-themed Bomberman game module."""

__all__ = ["BombermanGame"]


def __getattr__(name: str):  # pragma: no cover - simple proxy
    if name == "BombermanGame":
        from .bomberman import BombermanGame as _BombermanGame

        return _BombermanGame
    raise AttributeError(name)
