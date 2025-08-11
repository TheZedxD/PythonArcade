"""Simple enemy AI for Bomberman."""

from __future__ import annotations

import random
import pygame

from .level import TILE_SIZE, Level
from .bomb import Bomb
from .explosion import Explosion


class Enemy:
    def __init__(
        self, x: int, y: int, image: pygame.surface.Surface, speed: float = 0.5
    ):
        self.x = x
        self.y = y
        self.image = image
        self.speed = speed
        self.move_timer = 0.0
        self.change_timer = 0.0
        self.dir = (0, 0)

    def _choose_direction(self, level: Level, bombs: list[Bomb]) -> None:
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(dirs)
        for dx, dy in dirs:
            nx, ny = self.x + dx, self.y + dy
            blocked = level.is_blocked(nx, ny) or any(
                b.x == nx and b.y == ny for b in bombs
            )
            if not blocked:
                self.dir = (dx, dy)
                return
        self.dir = (0, 0)

    def update(
        self,
        dt: float,
        level: Level,
        bombs: list[Bomb],
        explosions: list[Explosion],
    ) -> bool:
        if any(e.x == self.x and e.y == self.y for e in explosions):
            return False
        self.move_timer -= dt
        self.change_timer -= dt
        if self.move_timer <= 0:
            nx, ny = self.x + self.dir[0], self.y + self.dir[1]
            if (
                self.dir == (0, 0)
                or level.is_blocked(nx, ny)
                or any(b.x == nx and b.y == ny for b in bombs)
            ):
                self.dir = (0, 0)
            else:
                self.x, self.y = nx, ny
            self.move_timer = self.speed
        if self.dir == (0, 0) or self.change_timer <= 0:
            self._choose_direction(level, bombs)
            self.change_timer = self.speed * 4
        if any(e.x == self.x and e.y == self.y for e in explosions):
            return False
        return True

    def draw(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
