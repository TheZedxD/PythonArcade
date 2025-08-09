import os
from unittest.mock import patch

import pygame

from ..game import Game


class KeyState(dict):
    """Mapping-like object for mocking key presses."""

    def __getitem__(self, key):
        return self.get(key, False)


def setup_game(num_players=2):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    pygame.display.set_mode((320, 240))
    g = Game()
    screen = pygame.display.get_surface()
    g.startup(screen, num_players=num_players)
    return g


def teardown_game():
    pygame.display.quit()
    pygame.quit()


def test_split_screen_layouts():
    g = setup_game(num_players=2)
    try:
        # Vertical layout by default
        assert len(g.cameras) == 2
        assert g.cameras[0].get_size() == (320, 120)
        assert g.cameras[1].get_size() == (320, 120)

        # Switch to horizontal layout and ensure surfaces resize correctly
        g.layout = "horizontal"
        g.create_cameras()
        assert g.cameras[0].get_size() == (160, 240)
        assert g.cameras[1].get_size() == (160, 240)
    finally:
        teardown_game()


def test_player_input_mapping():
    g = setup_game(num_players=2)
    try:
        # Press W to accelerate player 1 only
        with patch("pygame.key.get_pressed") as mock_pressed:
            mock_pressed.return_value = KeyState({pygame.K_w: True})
            speed0 = g.players[0].speed
            speed1 = g.players[1].speed
            g.update(0.016)
            assert g.players[0].speed > speed0
            assert g.players[1].speed == speed1

        # Press UP to accelerate player 2 only
        with patch("pygame.key.get_pressed") as mock_pressed:
            mock_pressed.return_value = KeyState({pygame.K_UP: True})
            speed0 = g.players[0].speed
            speed1 = g.players[1].speed
            g.update(0.016)
            # Player 1 speed should not increase when only player 2 input is pressed
            assert g.players[0].speed <= speed0
            assert g.players[1].speed > speed1
    finally:
        teardown_game()
