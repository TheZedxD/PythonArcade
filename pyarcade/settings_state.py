import pygame

from .common.theme import ACCENT_COLOR, BG_COLOR, PRIMARY_COLOR, draw_text
from .state import State
from .utils.persistence import load_json, save_json
from .utils.resources import save_path

SETTINGS_PATH = save_path("settings.json")
DEFAULT_SETTINGS = {
    "window_size": [800, 600],
    "fullscreen": False,
    "sound_volume": 1.0,
    "keybindings": {},
}
RESOLUTIONS = [(640, 480), (800, 600)]


class SettingsState(State):
    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        self.index = 0
        self.settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
        size = tuple(self.settings.get("window_size", RESOLUTIONS[1]))
        self.res_index = RESOLUTIONS.index(size) if size in RESOLUTIONS else 1
        self.options = ["Fullscreen", "Resolution", "Volume", "Back"]

    def handle_keyboard(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.options)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.adjust(-0.1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.adjust(0.1)
            elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                if self.options[self.index] == "Back" or event.key == pygame.K_ESCAPE:
                    save_json(SETTINGS_PATH, self.settings)
                    self.done = True
                    self.next = "menu"
                else:
                    self.adjust(0)

    def handle_gamepad(self, event):
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:
                if self.options[self.index] == "Back":
                    save_json(SETTINGS_PATH, self.settings)
                    self.done = True
                    self.next = "menu"
                else:
                    self.adjust(0)
            elif event.button in (1, 9):
                save_json(SETTINGS_PATH, self.settings)
                self.done = True
                self.next = "menu"
        elif event.type in (pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
            if event.type == pygame.JOYHATMOTION:
                x, y = event.value
            else:
                if event.axis == 0:
                    x, y = event.value, 0
                elif event.axis == 1:
                    x, y = 0, -event.value
                else:
                    return
            if y > 0.5 or y == 1:
                self.index = (self.index - 1) % len(self.options)
            elif y < -0.5 or y == -1:
                self.index = (self.index + 1) % len(self.options)
            elif x < -0.5 or x == -1:
                self.adjust(-0.1)
            elif x > 0.5 or x == 1:
                self.adjust(0.1)

    def adjust(self, delta):
        option = self.options[self.index]
        if option == "Fullscreen":
            if delta != 0:
                self.settings["fullscreen"] = not self.settings.get("fullscreen", False)
        elif option == "Resolution":
            if delta < 0:
                self.res_index = max(0, self.res_index - 1)
            elif delta > 0:
                self.res_index = min(len(RESOLUTIONS) - 1, self.res_index + 1)
            self.settings["window_size"] = list(RESOLUTIONS[self.res_index])
        elif option == "Volume":
            vol = self.settings.get("sound_volume", 1.0) + delta
            self.settings["sound_volume"] = max(0.0, min(1.0, round(vol, 2)))
            pygame.mixer.music.set_volume(self.settings["sound_volume"])

    def draw(self):
        self.screen.fill(BG_COLOR)
        width, height = self.screen.get_size()
        for i, option in enumerate(self.options):
            color = PRIMARY_COLOR if i == self.index else ACCENT_COLOR
            prefix = "> " if i == self.index else "  "
            if option == "Fullscreen":
                value = "On" if self.settings.get("fullscreen", False) else "Off"
            elif option == "Resolution":
                w, h = self.settings.get("window_size", RESOLUTIONS[self.res_index])
                value = f"{w}x{h}"
            elif option == "Volume":
                value = f"{self.settings.get('sound_volume', 1.0):.1f}"
            else:
                value = ""
            draw_text(
                self.screen,
                f"{prefix}{option} {value}",
                (width // 2, height // 3 + i * 40),
                32,
                color,
                center=True,
            )
