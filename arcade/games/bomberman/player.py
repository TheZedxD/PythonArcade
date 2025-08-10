"""Player logic for Bomberman."""
from __future__ import annotations

from dataclasses import dataclass
import pygame

from .level import TILE_SIZE, Level
from .bomb import Bomb


@dataclass
class Controls:
    up: int
    down: int
    left: int
    right: int
    bomb: int


class Player:
    def __init__(self, x: int, y: int, controls: Controls, image: pygame.surface.Surface):
        self.x = x
        self.y = y
        self.controls = controls
        self.image = image
        self.max_bombs = 1
        self.radius = 2

    @property
    def rect(self) -> pygame.rect.Rect:
        return pygame.Rect(self.x * TILE_SIZE, self.y * TILE_SIZE, TILE_SIZE, TILE_SIZE)

    def handle_input(self, keys: pygame.key.ScancodeWrapper, level: Level) -> None:
        dx = dy = 0
        if keys[self.controls.left]:
            dx = -1
        elif keys[self.controls.right]:
            dx = 1
        elif keys[self.controls.up]:
            dy = -1
        elif keys[self.controls.down]:
            dy = 1
        if dx or dy:
            nx, ny = self.x + dx, self.y + dy
            if not level.is_blocked(nx, ny):
                self.x, self.y = nx, ny

    def drop_bomb(self, bombs: list[Bomb], fuse_ms: int) -> None:
        if sum(1 for b in bombs if b.owner is self) >= self.max_bombs:
            return
        bombs.append(Bomb(self.x, self.y, fuse_ms, self.radius, owner=self))

    def draw(self, surface: pygame.surface.Surface) -> None:
        surface.blit(self.image, (self.x * TILE_SIZE, self.y * TILE_SIZE))
