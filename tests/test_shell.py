import os
import pygame

from arcade.game_loader import discover_games, load_game


def test_discover_and_run():
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    pygame.init()
    pygame.mixer.init()
    surface = pygame.Surface((64, 64))
    games = discover_games()
    assert games, "No games discovered"
    for info in games:
        game = load_game(info.entrypoint)
        game.init({"surface": surface})
        for _ in range(2):
            game.update(0.016)
            game.render(surface)
        game.shutdown()
    pygame.quit()
