import os
import importlib
import pygame

from arcade_menu import MainMenuState
from settings_state import SettingsState
from state import State
from utils.persistence import load_json, save_json

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {
    "window_size": [800, 600],
    "fullscreen": False,
    "sound_volume": 1.0,
    "keybindings": {}
}


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
    pygame.joystick.init()
    joysticks = []
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(joy)
    settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
    base_size = tuple(settings.get("window_size", [800, 600]))
    flags = pygame.SCALED | (pygame.FULLSCREEN if settings.get("fullscreen") else 0)
    screen = pygame.display.set_mode(base_size, flags)
    pygame.display.set_caption("Arcade")
    pygame.mixer.music.set_volume(settings.get("sound_volume", 1.0))
    clock = pygame.time.Clock()

    states = load_games()
    menu = MainMenuState()
    settings_state = SettingsState()
    states["menu"] = menu
    states["Settings"] = settings_state

    current_state = states["menu"]
    current_state.startup(screen)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                settings["fullscreen"] = not settings.get("fullscreen", False)
                flags = pygame.SCALED | (pygame.FULLSCREEN if settings.get("fullscreen") else 0)
                screen = pygame.display.set_mode(base_size, flags)
                for state in states.values():
                    state.screen = screen
                save_json(SETTINGS_PATH, settings)
            elif event.type in (pygame.JOYAXISMOTION, pygame.JOYBALLMOTION,
                                 pygame.JOYHATMOTION, pygame.JOYBUTTONDOWN,
                                 pygame.JOYBUTTONUP):
                current_state.handle_gamepad(event)
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
            if isinstance(current_state, SettingsState):
                settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
                pygame.mixer.music.set_volume(settings.get("sound_volume", 1.0))
                flags = pygame.SCALED | (pygame.FULLSCREEN if settings.get("fullscreen") else 0)
                screen = pygame.display.set_mode(base_size, flags)
                for state in states.values():
                    state.screen = screen
            if next_state:
                next_state.startup(screen, current_state.num_players)
                current_state = next_state

    pygame.quit()


if __name__ == "__main__":
    main()
