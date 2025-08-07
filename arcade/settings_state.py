import os
import pygame
from state import State
from utils.persistence import load_json, save_json

SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {
    "window_size": [800, 600],
    "fullscreen": False,
    "sound_volume": 1.0,
    "keybindings": {}
}


class SettingsState(State):
    def startup(self, screen):
        super().startup(screen)
        self.font = pygame.font.SysFont("Courier", 32)
        self.index = 0
        self.settings = load_json(SETTINGS_PATH, DEFAULT_SETTINGS)
        self.options = ["Fullscreen", "Volume", "Back"]

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

    def adjust(self, delta):
        option = self.options[self.index]
        if option == "Fullscreen":
            if delta != 0:
                self.settings["fullscreen"] = not self.settings.get("fullscreen", False)
        elif option == "Volume":
            vol = self.settings.get("sound_volume", 1.0) + delta
            self.settings["sound_volume"] = max(0.0, min(1.0, round(vol, 2)))
            pygame.mixer.music.set_volume(self.settings["sound_volume"])

    def draw(self):
        self.screen.fill((0, 0, 0))
        width, height = self.screen.get_size()
        for i, option in enumerate(self.options):
            color = (0, 255, 0) if i == self.index else (0, 155, 0)
            prefix = "> " if i == self.index else "  "
            if option == "Fullscreen":
                value = "On" if self.settings.get("fullscreen", False) else "Off"
            elif option == "Volume":
                value = f"{self.settings.get('sound_volume', 1.0):.1f}"
            else:
                value = ""
            text = self.font.render(f"{prefix}{option} {value}", True, color)
            rect = text.get_rect(center=(width // 2, height // 3 + i * 40))
            self.screen.blit(text, rect)
