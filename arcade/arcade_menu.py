import os
import random
import string
import json
import math
import pygame
from state import State

class MainMenuState(State):
    def __init__(self):
        super().__init__()
        self.options = []
        self.index = 0
        self.font = None
        self.title_font = None
        self.rain_font = None
        self.normal_color = (0, 155, 0)
        self.highlight_color = (0, 255, 0)
        self.bg_color = (0, 0, 0)
        self.rain_glyphs = []
        self.rain_chars = string.ascii_letters + string.digits
        self.rain_surfaces = {}
        self.phase = "game"
        self.selected_game = None

    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        self.num_players = 1
        self.font = pygame.font.SysFont("Courier", 32)
        self.title_font = pygame.font.SysFont("Courier", 48, bold=True)
        self.rain_font = pygame.font.SysFont("Courier", 20)
        self.rain_surfaces = {
            ch: self.rain_font.render(ch, True, self.normal_color)
            for ch in self.rain_chars
        }
        base_dir = os.path.join(os.path.dirname(__file__), "games")
        entries = []
        for name in os.listdir(base_dir):
            path = os.path.join(base_dir, name)
            module_file = os.path.join(path, "game.py")
            if os.path.isdir(path) and os.path.isfile(module_file):
                display = name
                meta_file = os.path.join(path, "meta.json")
                if os.path.isfile(meta_file):
                    try:
                        with open(meta_file, "r") as f:
                            meta = json.load(f)
                            display = meta.get("title", display)
                    except Exception:
                        pass
                else:
                    if display.startswith("game_"):
                        display = display[5:]
                    display = display.replace("_", " ").upper()
                entries.append((name, display))
        self.options = sorted(entries, key=lambda x: x[1])
        self.options.append(("Settings", "SETTINGS"))
        self.options.append(("Quit", "QUIT"))
        self.index = 0
        self.phase = "game"
        self.selected_game = None

        width, height = self.screen.get_size()
        max_glyphs = 100 if width >= 800 else 50
        self.rain_glyphs = []
        for _ in range(max_glyphs):
            x = random.randrange(0, width)
            y = random.randrange(-height, 0)
            speed = random.uniform(50, 150)
            char = random.choice(self.rain_chars)
            self.rain_glyphs.append([x, y, speed, char])

    def handle_keyboard(self, event):
        if self.phase == "game":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit = True
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.index = (self.index + 1) % len(self.options)
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.index = (self.index - 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    choice = self.options[self.index][0]
                    if choice == "Quit":
                        self.quit = True
                    elif choice == "Settings":
                        self.next = choice
                        self.done = True
                    else:
                        self.selected_game = choice
                        self.phase = "players"
        elif self.phase == "players":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_KP1):
                    self.num_players = 1
                    self.next = self.selected_game
                    self.done = True
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.num_players = 2
                    self.next = self.selected_game
                    self.done = True
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "game"

    def handle_gamepad(self, event):
        if self.phase == "game":
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    choice = self.options[self.index][0]
                    if choice == "Quit":
                        self.quit = True
                    elif choice == "Settings":
                        self.next = choice
                        self.done = True
                    else:
                        self.selected_game = choice
                        self.phase = "players"
                elif event.button in (1, 9):
                    self.quit = True
            elif event.type in (pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                if event.type == pygame.JOYHATMOTION:
                    x, y = event.value
                    vert = y
                else:
                    if event.axis != 1:
                        return
                    vert = -event.value
                if vert > 0.5 or vert == 1:
                    self.index = (self.index - 1) % len(self.options)
                elif vert < -0.5 or vert == -1:
                    self.index = (self.index + 1) % len(self.options)
        elif self.phase == "players":
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.num_players = 1
                    self.next = self.selected_game
                    self.done = True
                elif event.button == 1:
                    self.num_players = 2
                    self.next = self.selected_game
                    self.done = True
                elif event.button in (7, 9):
                    self.phase = "game"

    def update(self, dt):
        width, height = self.screen.get_size()
        for g in self.rain_glyphs:
            g[1] += g[2] * dt
            if g[1] > height:
                g[0] = random.randrange(0, width)
                g[1] = random.randrange(-height, 0)
                g[2] = random.uniform(50, 150)
                g[3] = random.choice(self.rain_chars)

    def draw(self):
        self.screen.fill(self.bg_color)
        width, height = self.screen.get_size()

        for x, y, _, char in self.rain_glyphs:
            glyph = self.rain_surfaces[char]
            self.screen.blit(glyph, (x, y))

        t = pygame.time.get_ticks() / 300.0
        glow = int(55 * (math.sin(t) + 1) / 2)
        title_color = (self.highlight_color[0],
                       min(255, self.highlight_color[1] + glow),
                       self.highlight_color[2])
        title = self.title_font.render("ARCADE TERMINAL", True, title_color)
        title_rect = title.get_rect(center=(width // 2, height // 5))
        self.screen.blit(title, title_rect)

        if self.phase == "game":
            for i, (_, label) in enumerate(self.options):
                color = self.highlight_color if i == self.index else self.normal_color
                prefix = "> " if i == self.index else "  "
                text = self.font.render(prefix + label, True, color)
                rect = text.get_rect(center=(width // 2, height // 3 + i * 40))
                self.screen.blit(text, rect)
        else:
            prompt = self.font.render("1 or 2 PLAYERS?", True, self.highlight_color)
            rect = prompt.get_rect(center=(width // 2, height // 2))
            self.screen.blit(prompt, rect)
