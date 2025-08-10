"""Power-up logic for Bomberman."""
from __future__ import annotations

import pygame

from .level import TILE_SIZE


class PowerUp:
    def __init__(self, x: int, y: int, kind: str, image: pygame.surface.Surface):
        self.x = x
        self.y = y
        self.kind = kind
        self.image = image

    def apply(self, player) -> None:
        if self.kind == "radius":
            player.radius += 1

    def draw(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
