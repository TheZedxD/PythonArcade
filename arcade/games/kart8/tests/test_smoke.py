import os

import pygame

from ..game import Game


def test_smoke():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((320, 240))
    g = Game()
    screen = pygame.display.get_surface()
    g.startup(screen)
    g.update(0.016)
    g.draw()
    pygame.display.quit()
    pygame.quit()
