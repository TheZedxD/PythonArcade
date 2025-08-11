"""Bomb logic for Bomberman."""

from __future__ import annotations

from typing import List, Optional, Tuple

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
        self.image: Optional[pygame.surface.Surface] = None

    def update(self, dt: float) -> bool:
        self.timer -= dt
        return self.timer <= 0

    def explode(
        self,
        level: Level,
        bombs: Optional[List["Bomb"]] = None,
    ) -> Tuple[List[Explosion], List[Tuple[int, int]]]:
        """Create explosion tiles and return destroyed bricks.

        Parameters
        ----------
        level:
            The level on which the bomb resides. Used for collision checks and
            destroying bricks.
        bombs:
            Optional list of active bombs. If provided, any bombs caught in the
            blast will immediately detonate, enabling chain reactions. Triggered
            bombs are removed from ``bombs`` and their resulting explosion tiles
            and destroyed bricks are merged into the return values.
        """

        tiles = [(self.x, self.y)]
        destroyed: List[Tuple[int, int]] = []
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dx, dy in dirs:
            for i in range(1, self.radius + 1):
                nx, ny = self.x + dx * i, self.y + dy * i
                if level.is_blocked(nx, ny):
                    if level.grid[ny][nx] == BRICK:
                        level.destroy(nx, ny)
                        tiles.append((nx, ny))
                        destroyed.append((nx, ny))
                    break
                tiles.append((nx, ny))

        explosions = [Explosion(x, y) for x, y in tiles]

        if bombs:
            triggered = [
                b for b in list(bombs) if (b.x, b.y) in tiles and b is not self
            ]
            for other in triggered:
                bombs.remove(other)
                exps, dest = other.explode(level, bombs)
                explosions.extend(exps)
                destroyed.extend(dest)

        return explosions, destroyed

    def draw(
        self, surface: pygame.surface.Surface, image: pygame.surface.Surface
    ) -> None:
        surface.blit(image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
