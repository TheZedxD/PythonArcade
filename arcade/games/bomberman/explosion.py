"""Explosion rendering for Bomberman."""
from __future__ import annotations

import pygame

from .level import TILE_SIZE


class Explosion:
    def __init__(self, x: int, y: int, duration: float = 0.3):
        self.x = x
        self.y = y
        self.timer = duration

    def update(self, dt: float) -> bool:
        self.timer -= dt
        return self.timer <= 0

    def draw(self, surface: pygame.surface.Surface, image: pygame.surface.Surface) -> None:
        surface.blit(image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
