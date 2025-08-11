from __future__ import annotations

from typing import Any, Protocol
import pygame

from .state import State

class IGame(Protocol):
    """Standard interface for arcade games."""

    def init(self, config: dict[str, Any]) -> None: ...
    def update(self, dt: float) -> None: ...
    def render(self, surface: pygame.Surface) -> None: ...
    def handle_event(self, event: pygame.event.Event) -> None: ...
    def shutdown(self) -> None: ...


class StateAdapter:
    """Adapter converting legacy State subclasses to the IGame protocol."""

    def __init__(self, state_cls: type[State]):
        self._state = state_cls()

    def init(self, config: dict[str, Any]) -> None:
        surface = config.get("surface")
        num_players = config.get("num_players", 1)
        opts = config.get("options", {})
        self._state.startup(surface, num_players, **opts)

    def update(self, dt: float) -> None:
        self._state.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        # Legacy states draw directly to their own screen
        self._state.draw()

    def handle_event(self, event: pygame.event.Event) -> None:
        self._state.get_event(event)

    def shutdown(self) -> None:
        self._state.cleanup()
