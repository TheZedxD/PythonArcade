import importlib
import logging
import os
import pathlib
import sys

import pygame

if __package__ in (None, ""):
    # Allow running this module directly, e.g. ``python pyarcade/main.py``
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from common.player_select import PlayerSelectOverlay
else:
    from .common.player_select import PlayerSelectOverlay

from pyarcade.arcade_menu import MainMenuState
from pyarcade.settings_state import SettingsState
from pyarcade.state import State
from pyarcade.ui.layout import init as layout_init
from pyarcade.utils.persistence import load_json, save_json
from pyarcade.utils.resources import save_path

SETTINGS_PATH = save_path("settings.json")
DEFAULT_SETTINGS = {
    "window_size": [800, 600],
    "fullscreen": False,
    "sound_volume": 1.0,
    "keybindings": {},
}


def load_games():
    """Import game state classes from the games package."""
    games = {}
    base_dir = os.path.join(os.path.dirname(__file__), "games")
    if not os.path.isdir(base_dir):
        return games
    for name in sorted(os.listdir(base_dir)):
        path = os.path.join(base_dir, name)
        module_file = os.path.join(path, "game.py")
        if os.path.isdir(path) and os.path.isfile(module_file):
            module_name = f".games.{name}.game"
            try:
                module = importlib.import_module(module_name, __package__)
                for attr in dir(module):
                    obj = getattr(module, attr)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, State)
                        and obj is not State
                    ):
                        games[name] = obj
                        logging.info("Loaded game: %s", name)
                        break
            except Exception:
                logging.exception("Failed to load game module '%s'", module_name)
                continue
    logging.info("Available games: %s", ", ".join(sorted(games)))
    return games


def main():
    log_file = save_path("arcade.log")
    logging.basicConfig(
        filename=str(log_file),
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    logging.info("Arcade launched")

    pygame.init()
    pygame.joystick.init()
    joysticks = []
    for i in range(pygame.joystick.get_count()):
        joy = pygame.joystick.Joystick(i)
        joy.init()
        joysticks.append(joy)
    settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
    base_size = tuple(settings.get("window_size", [800, 600]))
    flags = (
        pygame.SCALED
        | pygame.DOUBLEBUF
        | (pygame.FULLSCREEN if settings.get("fullscreen") else 0)
    )
    screen = pygame.display.set_mode(base_size, flags, vsync=1)
    layout_init(screen.get_size())
    pygame.display.set_caption("Arcade")
    pygame.mixer.music.set_volume(settings.get("sound_volume", 1.0))
    clock = pygame.time.Clock()

    game_classes = load_games()
    states: dict[str, State] = {}
    menu = MainMenuState()
    settings_state = SettingsState()
    states["menu"] = menu
    states["Settings"] = settings_state

    current_state_name = "menu"
    current_state = menu
    current_state.startup(screen)
    players_selected: int | None = None

    running = True
    while running:
        dt = clock.tick(getattr(current_state, "fps_cap", 60)) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                settings["fullscreen"] = not settings.get("fullscreen", False)
                flags = (
                    pygame.SCALED
                    | pygame.DOUBLEBUF
                    | (pygame.FULLSCREEN if settings.get("fullscreen") else 0)
                )
                screen = pygame.display.set_mode(base_size, flags, vsync=1)
                layout_init(screen.get_size())
                for state in states.values():
                    state.screen = screen
                save_json(SETTINGS_PATH, settings)
            elif event.type in (
                pygame.JOYAXISMOTION,
                pygame.JOYBALLMOTION,
                pygame.JOYHATMOTION,
                pygame.JOYBUTTONDOWN,
                pygame.JOYBUTTONUP,
            ):
                current_state.handle_gamepad(event)
            else:
                current_state.get_event(event)

        had_error = False
        try:
            current_state.update(dt)
            current_state.draw()
        except Exception:
            logging.exception(
                "Unhandled error in state '%s'", current_state.__class__.__name__
            )
            current_state.done = True
            current_state.next = "menu"
            had_error = True
        else:
            pygame.display.flip()
        if os.environ.get("PYARCADE_DEBUG_FPS") == "1":
            pygame.display.set_caption(f"Arcade {clock.get_fps():.1f} FPS")

        if current_state.quit:
            running = False
        elif current_state.done:
            next_name = current_state.next
            previous_state_name = current_state_name
            current_state.cleanup()
            if previous_state_name not in ("menu", "Settings"):
                states.pop(previous_state_name, None)
            if isinstance(current_state, SettingsState):
                settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
                pygame.mixer.music.set_volume(settings.get("sound_volume", 1.0))
                base_size = tuple(settings.get("window_size", [800, 600]))
                flags = (
                    pygame.SCALED
                    | pygame.DOUBLEBUF
                    | (pygame.FULLSCREEN if settings.get("fullscreen") else 0)
                )
                screen = pygame.display.set_mode(base_size, flags, vsync=1)
                layout_init(screen.get_size())
                for state in states.values():
                    state.screen = screen

            next_state: State | None = None
            num_players = getattr(current_state, "num_players", 1)
            if next_name:
                if next_name == "menu":
                    players_selected = None
                    next_state = states["menu"]
                    num_players = 1
                elif next_name == "Settings":
                    next_state = states["Settings"]
                elif next_name in game_classes:
                    if isinstance(current_state, MainMenuState):
                        selector = PlayerSelectOverlay()
                        players_selected = selector.run(screen)
                        current_state.num_players = players_selected
                    elif players_selected is None:
                        players_selected = getattr(current_state, "num_players", 1)
                    GameStateClass = game_classes[next_name]
                    next_state = GameStateClass(players=players_selected)
                    states[next_name] = next_state
                    num_players = players_selected
                else:
                    next_state = states.get(next_name)

            if next_state:
                opts = getattr(current_state, "game_options", {})
                logging.info(
                    "Transitioning to state '%s' (players=%s, options=%s)",
                    next_name,
                    num_players,
                    opts,
                )
                next_state.startup(screen, num_players, **opts)
                current_state = next_state
                current_state_name = next_name
                if had_error and next_name == "menu":
                    logging.info("Returned to main menu after error")

    pygame.quit()


if __name__ == "__main__":
    main()
