import os
import random
import string
from datetime import datetime
import pygame

from state import State
from utils.persistence import load_json, save_json

# Grid size
GRID_WIDTH = 10
GRID_HEIGHT = 20

# Path for high scores and settings
HS_PATH = os.path.join(os.path.dirname(__file__), "highscores.json")
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "settings.json")

# Tetromino definitions: list of rotations, each rotation is list of (x, y)
TETROMINOES = {
    "I": [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
    ],
    "J": [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    "L": [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
    "O": [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    "S": [
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
    ],
    "T": [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    "Z": [
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
    ],
}

# Score table for line clears
SCORES = {1: 40, 2: 100, 3: 300, 4: 1200}


class TetroidState(State):
    """Matrix-themed Tetris clone."""

    def startup(self, screen):
        super().startup(screen)
        self.font = pygame.font.SysFont("Courier", 24)
        self.big_font = pygame.font.SysFont("Courier", 32)
        self.rain_font = pygame.font.SysFont("Courier", 20)
        self.normal_color = (0, 155, 0)
        self.highlight_color = (0, 255, 0)
        self.bg_color = (0, 0, 0)
        self.cell = 24
        self.playfield_x = 50
        self.playfield_y = 20
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.drop_delay = 0.8
        self.drop_timer = 0
        self.state = "instructions"
        self.pause_options = ["Resume", "Volume -", "Volume +", "Fullscreen", "Quit"]
        self.pause_index = 0
        self.settings = load_json(SETTINGS_PATH, {
            "window_size": [800, 600],
            "fullscreen": False,
            "sound_volume": 1.0,
            "keybindings": {},
        })
        pygame.mixer.music.set_volume(self.settings.get("sound_volume", 1.0))
        self.hs_data = load_json(HS_PATH, {"highscore": 0, "plays": 0, "last_played": None})
        self.high_score = self.hs_data.get("highscore", 0)
        width, height = self.screen.get_size()
        self.rain_glyphs = []
        for _ in range(80):
            x = random.randrange(0, width)
            y = random.randrange(-height, 0)
            speed = random.uniform(50, 150)
            char = random.choice(string.ascii_letters + string.digits)
            self.rain_glyphs.append([x, y, speed, char])
        self.next_piece = self.random_piece()
        self.spawn_piece()

    # Piece management -------------------------------------------------
    def random_piece(self):
        shape = random.choice(list(TETROMINOES.keys()))
        return {"shape": shape, "rot": 0, "x": GRID_WIDTH // 2 - 2, "y": 0}

    def spawn_piece(self):
        self.current = self.next_piece
        self.current["x"] = GRID_WIDTH // 2 - 2
        self.current["y"] = 0
        self.current["rot"] = 0
        self.next_piece = self.random_piece()
        if self.collides(self.current, 0, 0):
            self.state = "gameover"
            self.update_stats()

    def rotate(self):
        old_rot = self.current["rot"]
        self.current["rot"] = (self.current["rot"] + 1) % len(TETROMINOES[self.current["shape"]])
        if self.collides(self.current, 0, 0):
            # try simple wall kicks
            for dx in (-1, 1, -2, 2):
                if not self.collides(self.current, dx, 0):
                    self.current["x"] += dx
                    return
            self.current["rot"] = old_rot

    def collides(self, piece, dx, dy):
        for x, y in TETROMINOES[piece["shape"]][piece["rot"]]:
            px = piece["x"] + x + dx
            py = piece["y"] + y + dy
            if px < 0 or px >= GRID_WIDTH or py < 0 or py >= GRID_HEIGHT:
                return True
            if self.grid[py][px]:
                return True
        return False

    def lock_piece(self):
        for x, y in TETROMINOES[self.current["shape"]][self.current["rot"]]:
            px = self.current["x"] + x
            py = self.current["y"] + y
            if 0 <= px < GRID_WIDTH and 0 <= py < GRID_HEIGHT:
                self.grid[py][px] = self.highlight_color

    def clear_lines(self):
        full = [i for i, row in enumerate(self.grid) if all(row)]
        for i in full:
            del self.grid[i]
            self.grid.insert(0, [None for _ in range(GRID_WIDTH)])
        if full:
            lines = len(full)
            self.score += SCORES.get(lines, lines * 100)
            self.lines += lines
            if self.lines // 10 + 1 > self.level:
                self.level += 1
                self.drop_delay = max(0.1, self.drop_delay * 0.8)
        return len(full)

    # Input and state --------------------------------------------------
    def handle_keyboard(self, event):
        if self.state == "instructions":
            if event.type == pygame.KEYDOWN:
                self.state = "play"
        elif self.state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and not self.collides(self.current, -1, 0):
                    self.current["x"] -= 1
                elif event.key == pygame.K_RIGHT and not self.collides(self.current, 1, 0):
                    self.current["x"] += 1
                elif event.key == pygame.K_DOWN and not self.collides(self.current, 0, 1):
                    self.current["y"] += 1
                elif event.key == pygame.K_UP:
                    self.rotate()
                elif event.key == pygame.K_SPACE:
                    while not self.collides(self.current, 0, 1):
                        self.current["y"] += 1
                elif event.key == pygame.K_ESCAPE:
                    self.state = "pause"
                    self.pause_index = 0
        elif self.state == "pause":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_index = (self.pause_index - 1) % len(self.pause_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_index = (self.pause_index + 1) % len(self.pause_options)
                elif event.key == pygame.K_RETURN:
                    choice = self.pause_options[self.pause_index]
                    if choice == "Resume":
                        self.state = "play"
                    elif choice == "Quit":
                        self.update_stats()
                        self.done = True
                        self.next = "menu"
                    elif choice == "Fullscreen":
                        pygame.display.toggle_fullscreen()
                        self.settings["fullscreen"] = not self.settings.get("fullscreen", False)
                        save_json(SETTINGS_PATH, self.settings)
                    elif choice == "Volume +":
                        vol = min(1.0, self.settings.get("sound_volume", 1.0) + 0.1)
                        self.settings["sound_volume"] = round(vol, 2)
                        pygame.mixer.music.set_volume(vol)
                        save_json(SETTINGS_PATH, self.settings)
                    elif choice == "Volume -":
                        vol = max(0.0, self.settings.get("sound_volume", 1.0) - 0.1)
                        self.settings["sound_volume"] = round(vol, 2)
                        pygame.mixer.music.set_volume(vol)
                        save_json(SETTINGS_PATH, self.settings)
                elif event.key == pygame.K_ESCAPE:
                    self.state = "play"
        elif self.state == "gameover":
            if event.type == pygame.KEYDOWN:
                self.done = True
                self.next = "menu"

    def update_stats(self):
        if self.score > self.high_score:
            self.high_score = self.score
        self.hs_data["highscore"] = self.high_score
        self.hs_data["plays"] = self.hs_data.get("plays", 0) + 1
        self.hs_data["last_played"] = datetime.now().isoformat()
        save_json(HS_PATH, self.hs_data)

    def update(self, dt):
        if self.state != "play":
            if self.state == "pause":
                pygame.mixer.music.set_volume(self.settings.get("sound_volume", 1.0))
            return
        width, height = self.screen.get_size()
        for g in self.rain_glyphs:
            g[1] += g[2] * dt
            if g[1] > height:
                g[0] = random.randrange(0, width)
                g[1] = random.randrange(-height, 0)
                g[2] = random.uniform(50, 150)
                g[3] = random.choice(string.ascii_letters + string.digits)

        self.drop_timer += dt
        if self.drop_timer >= self.drop_delay:
            self.drop_timer = 0
            if not self.collides(self.current, 0, 1):
                self.current["y"] += 1
            else:
                self.lock_piece()
                self.clear_lines()
                self.spawn_piece()

    # Drawing ----------------------------------------------------------
    def draw_cell(self, x, y, color):
        rect = pygame.Rect(self.playfield_x + x * self.cell,
                           self.playfield_y + y * self.cell,
                           self.cell, self.cell)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.normal_color, rect, 1)

    def draw_piece(self, piece, color):
        for x, y in TETROMINOES[piece["shape"]][piece["rot"]]:
            self.draw_cell(piece["x"] + x, piece["y"] + y, color)

    def draw(self):
        self.screen.fill(self.bg_color)
        width, height = self.screen.get_size()
        for x, y, _, char in self.rain_glyphs:
            glyph = self.rain_font.render(char, True, self.normal_color)
            self.screen.blit(glyph, (x, y))

        # Playfield border
        pf_rect = pygame.Rect(self.playfield_x - 4, self.playfield_y - 4,
                              GRID_WIDTH * self.cell + 8,
                              GRID_HEIGHT * self.cell + 8)
        pygame.draw.rect(self.screen, self.normal_color, pf_rect, 2)

        # Fixed blocks
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    self.draw_cell(x, y, self.grid[y][x])

        # Current and next pieces
        if self.state in ("play", "pause"):
            self.draw_piece(self.current, self.highlight_color)
        # Next piece preview
        preview_x = self.playfield_x + GRID_WIDTH * self.cell + 50
        preview_y = self.playfield_y + 50
        preview_rect = pygame.Rect(preview_x - 10, preview_y - 10, 100, 100)
        pygame.draw.rect(self.screen, self.normal_color, preview_rect, 2)
        for x, y in TETROMINOES[self.next_piece["shape"]][0]:
            px = preview_x + x * self.cell
            py = preview_y + y * self.cell
            rect = pygame.Rect(px, py, self.cell, self.cell)
            pygame.draw.rect(self.screen, self.highlight_color, rect)
            pygame.draw.rect(self.screen, self.normal_color, rect, 1)

        # Score
        score_text = self.font.render(f"Score: {self.score}", True, self.highlight_color)
        self.screen.blit(score_text, (preview_x, preview_y + 120))
        hs_text = self.font.render(f"High: {self.high_score}", True, self.highlight_color)
        self.screen.blit(hs_text, (preview_x, preview_y + 150))

        if self.state == "instructions":
            text1 = self.big_font.render("TETROID", True, self.highlight_color)
            text2 = self.font.render("Press any key", True, self.highlight_color)
            rect1 = text1.get_rect(center=(width // 2, height // 3))
            rect2 = text2.get_rect(center=(width // 2, height // 2))
            self.screen.blit(text1, rect1)
            self.screen.blit(text2, rect2)
        elif self.state == "pause":
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            for i, option in enumerate(self.pause_options):
                color = self.highlight_color if i == self.pause_index else self.normal_color
                prefix = "> " if i == self.pause_index else "  "
                text = self.big_font.render(prefix + option, True, color)
                rect = text.get_rect(center=(width // 2, height // 3 + i * 40))
                self.screen.blit(text, rect)
        elif self.state == "gameover":
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            text1 = self.big_font.render("GAME OVER", True, self.highlight_color)
            text2 = self.font.render("Press any key", True, self.highlight_color)
            rect1 = text1.get_rect(center=(width // 2, height // 3))
            rect2 = text2.get_rect(center=(width // 2, height // 2))
            self.screen.blit(text1, rect1)
            self.screen.blit(text2, rect2)
