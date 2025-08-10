"""Simple enemy AI for Bomberman."""

from __future__ import annotations

import random
import pygame

from .level import TILE_SIZE, Level


class Enemy:
    def __init__(self, x: int, y: int, image: pygame.surface.Surface):
        self.x = x
        self.y = y
        self.image = image
        self.move_timer = 0.0

    def update(self, dt: float, level: Level) -> None:
        self.move_timer -= dt
        if self.move_timer <= 0:
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            random.shuffle(dirs)
            for dx, dy in dirs:
                nx, ny = self.x + dx, self.y + dy
                if not level.is_blocked(nx, ny):
                    self.x, self.y = nx, ny
                    break
            self.move_timer = 0.5

    def draw(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
