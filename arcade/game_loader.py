from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .igame import IGame, StateAdapter

@dataclass
class GameInfo:
    title: str
    entrypoint: str
    description: str
    path: Path


def discover_games(base_dir: Path | None = None) -> List[GameInfo]:
    """Discover games under *base_dir* by reading ``game.json`` files."""
    base_dir = base_dir or Path(__file__).resolve().parent / "games"
    games: List[GameInfo] = []
    if not base_dir.exists():
        return games
    for sub in sorted(base_dir.iterdir()):
        if not sub.is_dir():
            continue
        meta_file = sub / "game.json"
        if not meta_file.is_file():
            continue
        try:
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            entrypoint = data["entrypoint"]
            # Attempt to import; skip if broken
            try:
                load_game(entrypoint)
            except Exception as e:  # pragma: no cover - warning path
                print(f"Warning: failed to load {entrypoint}: {e}")
                continue
            games.append(
                GameInfo(
                    title=data.get("title", sub.name),
                    entrypoint=entrypoint,
                    description=data.get("description", ""),
                    path=sub,
                )
            )
        except Exception as e:  # pragma: no cover - invalid metadata
            print(f"Warning: invalid metadata for {sub.name}: {e}")
    return games


def load_game(entrypoint: str) -> IGame:
    """Import *entrypoint* and return an :class:`IGame` implementation."""
    module_name, obj_name = entrypoint.split(":", 1)
    module = importlib.import_module(module_name)
    obj = getattr(module, obj_name)
    # Class based
    if isinstance(obj, type):
        if hasattr(obj, "startup") and hasattr(obj, "draw"):
            return StateAdapter(obj)
        instance = obj()
        if hasattr(instance, "startup") and hasattr(instance, "draw"):
            return StateAdapter(instance.__class__)
        return instance  # assume already IGame
    # Callable returning instance
    if callable(obj):
        instance = obj()
        if hasattr(instance, "startup") and hasattr(instance, "draw"):
            return StateAdapter(instance.__class__)
        return instance  # assume IGame
    raise TypeError(f"Unsupported entrypoint: {entrypoint}")

__all__ = ["discover_games", "load_game", "GameInfo"]
