import os
import random
import string
import json
import math
import pygame
from state import State
from common.theme import (
    ACCENT_COLOR,
    BG_COLOR,
    PRIMARY_COLOR,
    get_font,
)


class MainMenuState(State):
    fps_cap = 60

    def __init__(self):
        super().__init__()
        self.options = []
        self.index = 0
        self.font = None
        self.title_font = None
        self.rain_font = None
        self.normal_color = ACCENT_COLOR
        self.highlight_color = PRIMARY_COLOR
        self.bg_color = BG_COLOR
        self.rain_glyphs = []
        self.rain_chars = string.ascii_letters + string.digits
        self.rain_surfaces = {}
        self.phase = "game"
        self.selected_game = None
        self.option_surfaces = []
        self.option_positions = []
        self.prompt_players = None
        self.prompt_items = None
        self.prompt_rect = None
        self.title_base = None
        self.title_rect = None
        self.background = None
        self.menu_surface = None
        self.scanlines = None

    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        self.num_players = 1
        self.game_options = {}
        self.font = get_font(32)
        self.title_font = get_font(48, bold=True)
        self.rain_font = get_font(20)
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

        self._build_surfaces()

        width, height = self.screen.get_size()
        max_glyphs = 100 if width >= 800 else 50
        self.rain_glyphs = []
        for _ in range(max_glyphs):
            x = random.randrange(0, width)
            y = random.randrange(-height, 0)
            speed = random.uniform(50, 150)
            char = random.choice(self.rain_chars)
            self.rain_glyphs.append([x, y, speed, char])

    def _build_surfaces(self):
        width, height = self.screen.get_size()
        self.background = pygame.Surface((width, height)).convert()
        self.menu_surface = pygame.Surface(
            (width, height), pygame.SRCALPHA
        ).convert_alpha()
        self.scanlines = pygame.Surface(
            (width, height), pygame.SRCALPHA
        ).convert_alpha()
        for y in range(0, height, 2):
            pygame.draw.line(self.scanlines, (0, 0, 0, 40), (0, y), (width, y))
        self.rain_surfaces = {
            ch: self.rain_font.render(ch, True, self.normal_color).convert_alpha()
            for ch in self.rain_chars
        }
        self.option_surfaces = []
        self.option_positions = []
        y_start = height // 3
        for i, (_, label) in enumerate(self.options):
            normal = self.font.render(
                "  " + label, True, self.normal_color
            ).convert_alpha()
            highlight = self.font.render(
                "> " + label, True, self.highlight_color
            ).convert_alpha()
            rect = normal.get_rect(center=(width // 2, y_start + i * 40))
            self.option_surfaces.append((normal, highlight))
            self.option_positions.append(rect)
        self.prompt_players = self.font.render(
            "1 or 2 PLAYERS?", True, self.highlight_color
        ).convert_alpha()
        self.prompt_items = self.font.render(
            "ITEMS ON? Y/N", True, self.highlight_color
        ).convert_alpha()
        self.prompt_rect = self.prompt_players.get_rect(
            center=(width // 2, height // 2)
        )
        self.title_base = self.title_font.render(
            "ARCADE TERMINAL", True, PRIMARY_COLOR
        ).convert_alpha()
        self.title_rect = self.title_base.get_rect(center=(width // 2, height // 5))

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
                elif event.key in (pygame.K_2, pygame.K_KP2):
                    self.num_players = 2
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "game"
                    return
                else:
                    return
                if self.selected_game == "kart8":
                    self.phase = "items"
                else:
                    self.game_options = {}
                    self.next = self.selected_game
                    self.done = True
        elif self.phase == "items":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_1, pygame.K_KP1):
                    self.game_options = {"items": True}
                    self.next = self.selected_game
                    self.done = True
                elif event.key in (pygame.K_n, pygame.K_2, pygame.K_KP2):
                    self.game_options = {"items": False}
                    self.next = self.selected_game
                    self.done = True
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "players"

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
                elif event.button == 1:
                    self.num_players = 2
                elif event.button in (7, 9):
                    self.phase = "game"
                    return
                else:
                    return
                if self.selected_game == "kart8":
                    self.phase = "items"
                else:
                    self.game_options = {}
                    self.next = self.selected_game
                    self.done = True
        elif self.phase == "items":
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.game_options = {"items": True}
                    self.next = self.selected_game
                    self.done = True
                elif event.button == 1:
                    self.game_options = {"items": False}
                    self.next = self.selected_game
                    self.done = True
                elif event.button in (7, 9):
                    self.phase = "players"

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
        if self.background.get_size() != self.screen.get_size():
            self._build_surfaces()
        self.background.fill(self.bg_color)
        for x, y, _, char in self.rain_glyphs:
            glyph = self.rain_surfaces[char]
            self.background.blit(glyph, (x, y))
        self.screen.blit(self.background, (0, 0))

        self.menu_surface.fill((0, 0, 0, 0))
        t = pygame.time.get_ticks() / 300.0
        glow = int(55 * (math.sin(t) + 1) / 2)
        title = self.title_base.copy()
        title.fill((0, glow, 0), special_flags=pygame.BLEND_RGB_ADD)
        self.menu_surface.blit(title, self.title_rect)

        if self.phase == "game":
            for i, rect in enumerate(self.option_positions):
                surf = (
                    self.option_surfaces[i][1]
                    if i == self.index
                    else self.option_surfaces[i][0]
                )
                self.menu_surface.blit(surf, rect)
        elif self.phase == "players":
            self.menu_surface.blit(self.prompt_players, self.prompt_rect)
        else:
            self.menu_surface.blit(self.prompt_items, self.prompt_rect)

        self.screen.blit(self.menu_surface, (0, 0))
        self.screen.blit(self.scanlines, (0, 0))
