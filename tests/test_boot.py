"""Smoke test ensuring all games initialise without crashing."""

import os

import pygame

from arcade.main import load_games
from arcade.ui import layout


def test_boot_all_games():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    layout.init(screen.get_size())
    games = load_games()
    for state in games.values():
        state.startup(screen)
        state.update(0)
        state.draw()
    pygame.display.flip()
    pygame.quit()
