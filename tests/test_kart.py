import os
from unittest.mock import patch

import pygame

from arcade.games.kart8.engine.track import create_demo_track
from arcade.games.kart8.engine.physics import Car
from arcade.games.kart8.game import Game, NUM_LAPS


class KeyState(dict):
    """Mapping-like object for mocking key presses."""

    def __getitem__(self, key):
        return self.get(key, False)


def setup_game():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((320, 240))
    g = Game()
    screen = pygame.display.get_surface()
    g.startup(screen)
    return g


def teardown_game():
    pygame.display.quit()
    pygame.quit()


def test_deterministic_physics():
    track = create_demo_track()
    car1 = Car(track)
    controls = {"accelerate": True}
    for _ in range(10):
        car1.update(0.1, controls, False)
    speed1 = car1.speed

    car2 = Car(track)
    for _ in range(50):
        car2.update(0.02, controls, False)
    assert abs(speed1 - car2.speed) < 1e-5

    controls = {"brake": True}
    for _ in range(120):
        car1.update(1 / 60, controls, False)
    assert car1.speed <= 0.1


def test_checkpoint_lap_and_finish():
    g = setup_game()
    try:
        p = g.players[0]
        with patch("pygame.key.get_pressed") as mock_pressed:
            mock_pressed.return_value = KeyState({pygame.K_w: True})
            p.speed = p.max_speed
            frames = int((g.track.total_length / p.speed) * 60) * NUM_LAPS + 60
            for _ in range(frames):
                g.update(1 / 60)
        assert g.laps[0] >= NUM_LAPS
        assert g.finished[0] is True
    finally:
        teardown_game()
