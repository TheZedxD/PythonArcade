import os
import sys
import importlib
import pygame

from arcade_menu import MainMenuState
from state import State

WINDOW_SIZE = (800, 600)


def load_games():
    """Import game states from the games package."""
    games = {}
    base_dir = os.path.join(os.path.dirname(__file__), "games")
    if not os.path.isdir(base_dir):
        return games
    for name in sorted(os.listdir(base_dir)):
        path = os.path.join(base_dir, name)
        module_file = os.path.join(path, "game.py")
        if os.path.isdir(path) and os.path.isfile(module_file):
            module_name = f"games.{name}.game"
            try:
                module = importlib.import_module(module_name)
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if isinstance(obj, type) and issubclass(obj, State) and obj is not State:
                        games[name] = obj()
                        break
            except Exception:
                continue
    return games


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Arcade")
    clock = pygame.time.Clock()

    states = load_games()
    menu = MainMenuState()
    states["menu"] = menu

    current_state = states["menu"]
    current_state.startup(screen)

    fullscreen = False
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode(WINDOW_SIZE)
                for state in states.values():
                    state.screen = screen
            else:
                current_state.get_event(event)

        current_state.update(dt)
        current_state.draw()
        pygame.display.flip()

        if current_state.quit:
            running = False
        elif current_state.done:
            next_state = states.get(current_state.next)
            current_state.cleanup()
            if next_state:
                next_state.startup(screen)
                current_state = next_state

    pygame.quit()


if __name__ == "__main__":
    main()
