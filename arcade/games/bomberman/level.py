"""Level generation and grid utilities for Bomberman."""

from __future__ import annotations

import random
from typing import List

import pygame

TILE_SIZE = 32
# Tile constants
EMPTY, WALL, BRICK = 0, 1, 2


class Level:
    """Represents a grid of walls and bricks."""

    def __init__(self, size: tuple[int, int]):
        self.width, self.height = size
        self.grid: List[List[int]] = [
            [EMPTY for _ in range(self.width)] for _ in range(self.height)
        ]
        self.generate()

    def generate(self) -> None:
        """Generate random walls and bricks."""
        for y in range(self.height):
            for x in range(self.width):
                if x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                    self.grid[y][x] = WALL
                elif x % 2 == 0 and y % 2 == 0:
                    self.grid[y][x] = WALL
                else:
                    # leave spawn areas empty
                    if (x, y) in {
                        (1, 1),
                        (1, 2),
                        (2, 1),
                        (self.width - 2, self.height - 2),
                        (self.width - 3, self.height - 2),
                        (self.width - 2, self.height - 3),
                    }:
                        continue
                    if random.random() < 0.7:
                        self.grid[y][x] = BRICK

    def is_blocked(self, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return self.grid[y][x] in (WALL, BRICK)

    def destroy(self, x: int, y: int) -> None:
        if self.grid[y][x] == BRICK:
            self.grid[y][x] = EMPTY

    def draw(
        self, surface: pygame.surface.Surface, assets: dict[str, pygame.surface.Surface]
    ) -> None:
        for y in range(self.height):
            for x in range(self.width):
                tile = self.grid[y][x]
                pos = (x * TILE_SIZE, y * TILE_SIZE)
                if tile == WALL:
                    surface.blit(assets["wall"], pos)
                elif tile == BRICK:
                    surface.blit(assets["brick"], pos)
                else:
                    pygame.draw.rect(
                        surface, (0, 0, 0), (pos[0], pos[1], TILE_SIZE, TILE_SIZE)
                    )
                # grid lines
                pygame.draw.rect(
                    surface, (0, 40, 0), (pos[0], pos[1], TILE_SIZE, TILE_SIZE), 1
                )
