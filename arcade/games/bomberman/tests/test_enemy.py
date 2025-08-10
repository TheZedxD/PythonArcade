import pygame
import pathlib, sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[4]))

from arcade.games.bomberman.level import Level, EMPTY, BRICK
from arcade.games.bomberman.enemy import Enemy
from arcade.games.bomberman.bomb import Bomb
from arcade.games.bomberman.explosion import Explosion


def empty_level(w=5, h=5):
    lvl = Level.generate_random(w, h, seed=1)
    # clear bricks for predictable movement
    for y in range(h):
        for x in range(w):
            if lvl.grid[y][x] == BRICK:
                lvl.grid[y][x] = EMPTY
    return lvl


def test_enemy_avoids_bombs_and_dies():
    pygame.init()
    lvl = empty_level()
    enemy = Enemy(2, 2, pygame.Surface((1, 1)), speed=0.1)
    bomb = Bomb(3, 2, 1000, 1)
    enemy.dir = (1, 0)
    enemy.update(0.2, lvl, [bomb], [])
    assert (enemy.x, enemy.y) == (2, 2)
    dead = not enemy.update(0.2, lvl, [], [Explosion(2, 2)])
    assert dead
    pygame.quit()
