"""Core logic tests for the Bomberman mini game.

These tests exercise the bomb explosion logic, including chain reactions and
tile based damage rules. They run headless using pygame's dummy video driver so
they can execute in CI environments without a display.
"""

from __future__ import annotations

import os
import pathlib
import sys

import pygame

# Ensure the project root is importable
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from arcade.games.bomberman.level import Level, EMPTY, WALL, BRICK
from arcade.games.bomberman.bomb import Bomb
from arcade.games.bomberman.enemy import Enemy


def make_empty_level(w: int = 7, h: int = 5) -> Level:
    """Return a level with all tiles set to ``EMPTY`` for test control."""

    lvl = Level.generate_random(w, h, seed=1)
    for y in range(h):
        for x in range(w):
            lvl.grid[y][x] = EMPTY
    return lvl


def setup_pygame() -> None:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()


def teardown_pygame() -> None:
    pygame.quit()


def test_chain_reaction_destroys_soft_block():
    setup_pygame()
    lvl = make_empty_level()
    # place a brick two tiles to the right of the first bomb
    lvl.grid[2][4] = BRICK
    b1 = Bomb(1, 2, 1000, 2)
    b2 = Bomb(3, 2, 1000, 1)
    bombs = [b1, b2]

    # detonate first bomb; it should trigger the second and destroy the brick
    b1.explode(lvl, bombs)
    assert lvl.grid[2][4] == EMPTY
    assert b2 not in bombs
    teardown_pygame()


def test_hard_block_stops_ray():
    setup_pygame()
    lvl = make_empty_level()
    lvl.grid[1][2] = WALL
    lvl.grid[1][3] = BRICK
    bomb = Bomb(1, 1, 1000, 3)
    bomb.explode(lvl)
    # brick beyond the wall should remain
    assert lvl.grid[1][3] == BRICK
    teardown_pygame()


def test_enemy_damage_only_in_ray():
    setup_pygame()
    lvl = make_empty_level()
    bomb = Bomb(1, 1, 1000, 2)
    explosions, _ = bomb.explode(lvl)
    e_hit = Enemy(2, 1, pygame.Surface((1, 1)), speed=0.1)
    e_safe = Enemy(2, 2, pygame.Surface((1, 1)), speed=0.1)
    assert not e_hit.update(0.1, lvl, [], explosions)
    assert e_safe.update(0.1, lvl, [], explosions)
    teardown_pygame()


def test_headless_tick_loop():
    setup_pygame()
    from arcade.games.bomberman.bomberman import BombermanGame

    screen = pygame.Surface((320, 240))
    game = BombermanGame()
    game.startup(screen, num_players=1)
    for _ in range(3):
        game.update(0.1)
    # no assertion; test passes if no exceptions are raised
    teardown_pygame()

