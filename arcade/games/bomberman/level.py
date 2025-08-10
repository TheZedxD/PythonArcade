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
        self.rects = [
            [
                (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                for x in range(self.width)
            ]
            for y in range(self.height)
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

    @classmethod
    def generate_random(
        cls, width: int, height: int, seed: int | None = None
    ) -> "Level":
        """Create a new level with deterministic randomness.

        Parameters
        ----------
        width, height:
            Size of the level in tiles.
        seed:
            Optional seed to make generation deterministic. If ``None`` a
            random seed is used.

        The resulting map always leaves player spawn tiles empty and carves a
        simple corridor ensuring there is at least one valid path for enemies
        to roam without needing to destroy bricks.
        """

        rng = random.Random(seed)
        level = cls((width, height))
        grid: List[List[int]] = [[EMPTY for _ in range(width)] for _ in range(height)]
        for y in range(height):
            for x in range(width):
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    grid[y][x] = WALL
                elif x % 2 == 0 and y % 2 == 0:
                    grid[y][x] = WALL
                else:
                    if (x, y) in {
                        (1, 1),
                        (1, 2),
                        (2, 1),
                        (width - 2, height - 2),
                        (width - 3, height - 2),
                        (width - 2, height - 3),
                    }:
                        continue
                    if rng.random() < 0.7:
                        grid[y][x] = BRICK
        # carve a guaranteed path from top-left to bottom-right
        for x in range(1, width - 1):
            grid[1][x] = EMPTY
        for y in range(1, height - 1):
            grid[y][width - 2] = EMPTY
        level.grid = grid
        return level

    def is_blocked(self, x: int, y: int) -> bool:
        if x < 0 or y < 0 or x >= self.width or y >= self.height:
            return True
        return self.grid[y][x] in (WALL, BRICK)

    def destroy(self, x: int, y: int) -> bool:
        """Remove a brick tile and return True if destroyed."""

        if self.grid[y][x] == BRICK:
            self.grid[y][x] = EMPTY
            return True
        return False

    def draw(
        self, surface: pygame.surface.Surface, assets: dict[str, pygame.surface.Surface]
    ) -> None:
        wall = assets.get("wall")
        brick = assets.get("brick")
        for y in range(self.height):
            for x in range(self.width):
                tile = self.grid[y][x]
                rect = self.rects[y][x]
                if tile == WALL:
                    if wall:
                        surface.blit(wall, rect[:2])
                    else:
                        pygame.draw.rect(surface, (0, 40, 0), rect)
                elif tile == BRICK:
                    if brick:
                        surface.blit(brick, rect[:2])
                    else:
                        pygame.draw.rect(surface, (0, 80, 0), rect)
                else:
                    pygame.draw.rect(surface, (0, 0, 0), rect)
                pygame.draw.rect(surface, (0, 40, 0), rect, 1)
