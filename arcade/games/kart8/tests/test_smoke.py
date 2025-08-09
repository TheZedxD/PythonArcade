import pygame
from ..game import Game

def test_smoke():
    pygame.init()
    screen = pygame.Surface((320, 240))
    g = Game()
    g.startup(screen)
    g.update(0.016)
    g.draw()
    pygame.quit()
