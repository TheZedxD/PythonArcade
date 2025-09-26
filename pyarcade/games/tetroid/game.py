import random
import string
from datetime import datetime

import pygame

from ...common.theme import ACCENT_COLOR, BG_COLOR, PRIMARY_COLOR, draw_text, get_font
from ...common.ui import PauseMenu, apply_pause_option
from ...state import State
from ...utils.persistence import load_json, save_json
from ...utils.resources import save_path

# Grid size
GRID_WIDTH = 10
GRID_HEIGHT = 20

# Path for high scores and settings
HS_PATH = save_path("tetroid_highscores.json")
SETTINGS_PATH = save_path("settings.json")

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

    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        self.rain_font = get_font(20)
        self.rain_chars = string.ascii_letters + string.digits
        self.rain_surfaces = {
            ch: self.rain_font.render(ch, True, ACCENT_COLOR) for ch in self.rain_chars
        }
        self.normal_color = ACCENT_COLOR
        self.highlight_color = PRIMARY_COLOR
        self.bg_color = BG_COLOR
        self.cell = 24
        playfield_width = GRID_WIDTH * self.cell
        gap = 100
        screen_width, _ = self.screen.get_size()
        if self.num_players == 2:
            total_width = playfield_width * 2 + gap
            self.playfield_x = (screen_width - total_width) // 2
        else:
            self.playfield_x = (screen_width - playfield_width) // 2
        self.playfield_y = 20
        # Boards for each player.  board1 is always present; board2 is
        # created only for two-player games.
        self.board1 = self._create_board(self.playfield_x)
        self.board2 = None
        self.score = 0
        self.score2 = 0
        if self.num_players == 2:
            self.board2 = self._create_board(self.playfield_x + playfield_width + gap)
            self.score2 = 0
        self.state = "instructions"
        self.pause_menu = PauseMenu(
            ["Resume", "Volume -", "Volume +", "Fullscreen", "Quit"], font_size=32
        )
        self.settings = load_json(
            SETTINGS_PATH,
            {
                "window_size": [800, 600],
                "fullscreen": False,
                "sound_volume": 1.0,
                "keybindings": {},
            },
        )
        pygame.mixer.music.set_volume(self.settings.get("sound_volume", 1.0))
        self.hs_data = load_json(
            HS_PATH, {"highscore": 0, "plays": 0, "last_played": None}
        )
        self.high_score = self.hs_data.get("highscore", 0)
        width, height = self.screen.get_size()
        max_glyphs = 80 if width >= 800 else 40
        self.rain_glyphs = []
        for _ in range(max_glyphs):
            x = random.randrange(0, width)
            y = random.randrange(-height, 0)
            speed = random.uniform(50, 150)
            char = random.choice(self.rain_chars)
            self.rain_glyphs.append([x, y, speed, char])
        self.overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        # Initialize first pieces for the board(s)
        self.spawn_piece(self.board1)
        if self.board2:
            self.spawn_piece(self.board2)

    # Piece management -------------------------------------------------
    def random_piece(self):
        shape = random.choice(list(TETROMINOES.keys()))
        return {"shape": shape, "rot": 0, "x": GRID_WIDTH // 2 - 2, "y": 0}

    def _create_board(self, playfield_x):
        board = {
            "playfield_x": playfield_x,
            "playfield_y": self.playfield_y,
            "grid": [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)],
            "score": 0,
            "lines": 0,
            "level": 1,
            "drop_delay": 0.8,
            "drop_timer": 0,
            "next_piece": self.random_piece(),
            "current": None,
            "gameover": False,
        }
        return board

    def spawn_piece(self, board):
        board["current"] = board["next_piece"]
        board["current"]["x"] = GRID_WIDTH // 2 - 2
        board["current"]["y"] = 0
        board["current"]["rot"] = 0
        board["next_piece"] = self.random_piece()
        if self.collides(board, board["current"], 0, 0):
            board["gameover"] = True
            if self.num_players == 1 or (
                self.board1["gameover"] and (not self.board2 or self.board2["gameover"])
            ):
                self.state = "gameover"
                self.update_stats()

    def rotate(self, board):
        piece = board["current"]
        old_rot = piece["rot"]
        piece["rot"] = (piece["rot"] + 1) % len(TETROMINOES[piece["shape"]])
        if self.collides(board, piece, 0, 0):
            # try simple wall kicks
            for dx in (-1, 1, -2, 2):
                if not self.collides(board, piece, dx, 0):
                    piece["x"] += dx
                    return
            piece["rot"] = old_rot

    def collides(self, board, piece, dx, dy):
        grid = board["grid"]
        for x, y in TETROMINOES[piece["shape"]][piece["rot"]]:
            px = piece["x"] + x + dx
            py = piece["y"] + y + dy
            if px < 0 or px >= GRID_WIDTH or py < 0 or py >= GRID_HEIGHT:
                return True
            if grid[py][px]:
                return True
        return False

    def lock_piece(self, board):
        grid = board["grid"]
        piece = board["current"]
        for x, y in TETROMINOES[piece["shape"]][piece["rot"]]:
            px = piece["x"] + x
            py = piece["y"] + y
            if 0 <= px < GRID_WIDTH and 0 <= py < GRID_HEIGHT:
                grid[py][px] = self.highlight_color

    def clear_lines(self, board):
        grid = board["grid"]
        full = [i for i, row in enumerate(grid) if all(row)]
        for i in full:
            del grid[i]
            grid.insert(0, [None for _ in range(GRID_WIDTH)])
        if full:
            lines = len(full)
            board["score"] += SCORES.get(lines, lines * 100)
            board["lines"] += lines
            if board["lines"] // 10 + 1 > board["level"]:
                board["level"] += 1
                board["drop_delay"] = max(0.1, board["drop_delay"] * 0.8)
        return len(full)

    # Input and state --------------------------------------------------
    def handle_keyboard(self, event):
        if self.state == "instructions":
            if event.type == pygame.KEYDOWN:
                self.state = "play"
        elif self.state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "pause"
                    self.pause_menu.index = 0
                # Player 1 controls
                if not self.board1["gameover"]:
                    if event.key == pygame.K_LEFT and not self.collides(
                        self.board1, self.board1["current"], -1, 0
                    ):
                        self.board1["current"]["x"] -= 1
                    elif event.key == pygame.K_RIGHT and not self.collides(
                        self.board1, self.board1["current"], 1, 0
                    ):
                        self.board1["current"]["x"] += 1
                    elif event.key == pygame.K_DOWN and not self.collides(
                        self.board1, self.board1["current"], 0, 1
                    ):
                        self.board1["current"]["y"] += 1
                    elif event.key == pygame.K_UP:
                        self.rotate(self.board1)
                    elif event.key == pygame.K_SPACE:
                        while not self.collides(
                            self.board1, self.board1["current"], 0, 1
                        ):
                            self.board1["current"]["y"] += 1
                # Player 2 controls
                if (
                    self.num_players == 2
                    and self.board2
                    and not self.board2["gameover"]
                ):
                    if event.key == pygame.K_a and not self.collides(
                        self.board2, self.board2["current"], -1, 0
                    ):
                        self.board2["current"]["x"] -= 1
                    elif event.key == pygame.K_d and not self.collides(
                        self.board2, self.board2["current"], 1, 0
                    ):
                        self.board2["current"]["x"] += 1
                    elif event.key == pygame.K_s and not self.collides(
                        self.board2, self.board2["current"], 0, 1
                    ):
                        self.board2["current"]["y"] += 1
                    elif event.key == pygame.K_w:
                        self.rotate(self.board2)
                    elif event.key == pygame.K_f:
                        while not self.collides(
                            self.board2, self.board2["current"], 0, 1
                        ):
                            self.board2["current"]["y"] += 1
        elif self.state == "pause":
            choice = self.pause_menu.handle_keyboard(event)
            if choice:
                if choice == "Resume":
                    self.state = "play"
                elif choice == "Quit":
                    self.update_stats()
                    self.done = True
                    self.next = "menu"
                else:
                    apply_pause_option(choice, self.settings, SETTINGS_PATH)
        elif self.state == "gameover":
            if event.type == pygame.KEYDOWN:
                self.done = True
                self.next = "menu"

    def handle_gamepad(self, event):
        if self.state == "instructions":
            if event.type == pygame.JOYBUTTONDOWN:
                self.state = "play"
        elif self.state == "play":
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    self.rotate(self.board1)
                elif event.button == 1:
                    while not self.collides(self.board1, self.board1["current"], 0, 1):
                        self.board1["current"]["y"] += 1
                elif event.button in (7, 9):
                    self.state = "pause"
                    self.pause_menu.index = 0
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    if event.value < -0.5 and not self.collides(
                        self.board1, self.board1["current"], -1, 0
                    ):
                        self.board1["current"]["x"] -= 1
                    elif event.value > 0.5 and not self.collides(
                        self.board1, self.board1["current"], 1, 0
                    ):
                        self.board1["current"]["x"] += 1
                elif event.axis == 1:
                    if event.value > 0.5 and not self.collides(
                        self.board1, self.board1["current"], 0, 1
                    ):
                        self.board1["current"]["y"] += 1
            elif event.type == pygame.JOYHATMOTION:
                x, y = event.value
                if x == -1 and not self.collides(
                    self.board1, self.board1["current"], -1, 0
                ):
                    self.board1["current"]["x"] -= 1
                elif x == 1 and not self.collides(
                    self.board1, self.board1["current"], 1, 0
                ):
                    self.board1["current"]["x"] += 1
                if y == -1 and not self.collides(
                    self.board1, self.board1["current"], 0, 1
                ):
                    self.board1["current"]["y"] += 1
                elif y == 1:
                    self.rotate(self.board1)
        elif self.state == "pause":
            choice = self.pause_menu.handle_gamepad(event)
            if choice:
                if choice == "Resume":
                    self.state = "play"
                elif choice == "Quit":
                    self.update_stats()
                    self.done = True
                    self.next = "menu"
                else:
                    apply_pause_option(choice, self.settings, SETTINGS_PATH)
        elif self.state == "gameover":
            if event.type == pygame.JOYBUTTONDOWN:
                self.done = True
                self.next = "menu"

    def update_stats(self):
        best = self.board1["score"]
        if self.board2:
            best = max(best, self.board2["score"])
        if best > self.high_score:
            self.high_score = best
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

        boards = [self.board1]
        if self.board2:
            boards.append(self.board2)
        for board in boards:
            if board["gameover"]:
                continue
            board["drop_timer"] += dt
            if board["drop_timer"] >= board["drop_delay"]:
                board["drop_timer"] = 0
                if not self.collides(board, board["current"], 0, 1):
                    board["current"]["y"] += 1
                else:
                    self.lock_piece(board)
                    self.clear_lines(board)
                    self.spawn_piece(board)

        self.score = self.board1["score"]
        if self.board2:
            self.score2 = self.board2["score"]

    # Drawing ----------------------------------------------------------
    def draw_cell(self, board, x, y, color):
        rect = pygame.Rect(
            board["playfield_x"] + x * self.cell,
            board["playfield_y"] + y * self.cell,
            self.cell,
            self.cell,
        )
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, self.normal_color, rect, 1)

    def draw_piece(self, board, piece, color):
        for x, y in TETROMINOES[piece["shape"]][piece["rot"]]:
            self.draw_cell(board, piece["x"] + x, piece["y"] + y, color)

    def draw(self):
        self.screen.fill(self.bg_color)
        width, height = self.screen.get_size()
        for x, y, _, char in self.rain_glyphs:
            glyph = self.rain_surfaces[char]
            self.screen.blit(glyph, (x, y))

        boards = [self.board1]
        if self.board2:
            boards.append(self.board2)
        for idx, board in enumerate(boards):
            pf_rect = pygame.Rect(
                board["playfield_x"] - 4,
                board["playfield_y"] - 4,
                GRID_WIDTH * self.cell + 8,
                GRID_HEIGHT * self.cell + 8,
            )
            pygame.draw.rect(self.screen, self.normal_color, pf_rect, 2)

            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if board["grid"][y][x]:
                        self.draw_cell(board, x, y, board["grid"][y][x])

            if self.state in ("play", "pause") and not board["gameover"]:
                self.draw_piece(board, board["current"], self.highlight_color)

            preview_x = board["playfield_x"] + GRID_WIDTH * self.cell + 50
            preview_y = board["playfield_y"] + 50
            preview_rect = pygame.Rect(preview_x - 10, preview_y - 10, 100, 100)
            pygame.draw.rect(self.screen, self.normal_color, preview_rect, 2)
            for x, y in TETROMINOES[board["next_piece"]["shape"]][0]:
                px = preview_x + x * self.cell
                py = preview_y + y * self.cell
                rect = pygame.Rect(px, py, self.cell, self.cell)
                pygame.draw.rect(self.screen, self.highlight_color, rect)
                pygame.draw.rect(self.screen, self.normal_color, rect, 1)

            label = (
                f"P{idx + 1}: {board['score']}"
                if self.board2
                else f"Score: {board['score']}"
            )
            draw_text(self.screen, label, (preview_x, preview_y + 120), 24)
            if idx == 0:
                draw_text(
                    self.screen,
                    f"High: {self.high_score}",
                    (preview_x, preview_y + 150),
                    24,
                )

        if self.state == "instructions":
            draw_text(
                self.screen,
                "TETROID",
                (width // 2, height // 3),
                32,
                center=True,
            )
            if self.board2:
                draw_text(
                    self.screen,
                    "P1: Arrows  P2: WASD",
                    (width // 2, height // 2),
                    24,
                    center=True,
                )
                draw_text(
                    self.screen,
                    "Press any key",
                    (width // 2, height // 2 + 40),
                    24,
                    center=True,
                )
            else:
                draw_text(
                    self.screen,
                    "Press any key",
                    (width // 2, height // 2),
                    24,
                    center=True,
                )
        elif self.state == "pause":
            self.overlay.fill((*self.bg_color, 200))
            self.pause_menu.draw(self.overlay)
            self.screen.blit(self.overlay, (0, 0))
        elif self.state == "gameover":
            self.overlay.fill((*self.bg_color, 200))
            self.screen.blit(self.overlay, (0, 0))
            draw_text(
                self.screen,
                "GAME OVER",
                (width // 2, height // 3),
                32,
                center=True,
            )
            draw_text(
                self.screen,
                "Press any key",
                (width // 2, height // 2),
                24,
                center=True,
            )
