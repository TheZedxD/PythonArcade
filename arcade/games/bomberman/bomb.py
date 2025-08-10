"""Bomb logic for Bomberman."""

from __future__ import annotations

import pygame

from .level import TILE_SIZE, Level, BRICK
from .explosion import Explosion


class Bomb:
    def __init__(self, x: int, y: int, fuse_ms: int, radius: int, *, owner=None):
        self.x = x
        self.y = y
        self.timer = fuse_ms / 1000.0
        self.radius = radius
        self.owner = owner
        self.image: pygame.surface.Surface | None = None

    def update(self, dt: float) -> bool:
        self.timer -= dt
        return self.timer <= 0

    def explode(self, level: Level) -> list[Explosion]:
        tiles = [(self.x, self.y)]
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in dirs:
            for i in range(1, self.radius + 1):
                nx, ny = self.x + dx * i, self.y + dy * i
                if level.is_blocked(nx, ny):
                    if level.grid[ny][nx] == BRICK:
                        level.destroy(nx, ny)
                        tiles.append((nx, ny))
                    break
                tiles.append((nx, ny))
        return [Explosion(x, y) for x, y in tiles]

    def draw(
        self, surface: pygame.surface.Surface, image: pygame.surface.Surface
    ) -> None:
        surface.blit(image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
