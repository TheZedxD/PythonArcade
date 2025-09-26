import random
import string
from datetime import datetime

import pygame

from ...state import State
from ...utils.persistence import load_json, save_json
from ...utils.resources import save_path

# Grid dimensions for Virus bottle
GRID_WIDTH = 8
GRID_HEIGHT = 16

# Paths for high scores and settings
HS_PATH = save_path("virus_highscores.json")
SETTINGS_PATH = save_path("settings.json")

# Color palette for pills and viruses (RGB values)
COLORS = [(255, 0, 0), (0, 0, 255), (255, 255, 0)]  # Red  # Blue  # Yellow


class VirusState(State):
    """Virus (Dr. Mario clone) game state with a Matrix-style aesthetic."""

    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        # Initialize fonts (using a terminal-style font)
        self.font = pygame.font.SysFont("Courier", 24)
        self.big_font = pygame.font.SysFont("Courier", 32, bold=True)
        self.rain_font = pygame.font.SysFont("Courier", 20)
        # Color scheme (Matrix green on black)
        self.normal_color = (0, 155, 0)
        self.highlight_color = (0, 255, 0)
        self.bg_color = (0, 0, 0)
        # Cell size and playfield positioning
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
        # Initialize boards for one or two players
        self.board1 = self._create_board(self.playfield_x)
        self.board2 = None
        self.score = 0
        self.score2 = 0
        if self.num_players == 2:
            self.board2 = self._create_board(self.playfield_x + playfield_width + gap)
            self.score2 = 0
        # Place initial viruses on board1 (and copy to board2 for fairness in 2P)
        self._init_viruses(self.board1)
        if self.board2:
            # Copy the same virus layout and colors to player 2's board
            self.board2["grid"] = [row[:] for row in self.board1["grid"]]
            self.board2["viruses"] = set(self.board1["viruses"])
        # Prepare first falling pieces
        self.board1["next_piece"] = self._random_piece()
        self.board1["current"] = None
        if self.board2:
            self.board2["next_piece"] = self._random_piece()
            self.board2["current"] = None
        # Game state flags
        self.state = "instructions"
        self.pause_options = ["Resume", "Volume -", "Volume +", "Fullscreen", "Quit"]
        self.pause_index = 0
        # Load settings (volume, fullscreen) and apply volume
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
        # Load high score data
        self.hs_data = load_json(
            HS_PATH, {"highscore": 0, "plays": 0, "last_played": None}
        )
        self.high_score = self.hs_data.get("highscore", 0)
        # Initialize Matrix-style falling code background
        width, height = self.screen.get_size()
        self.rain_glyphs = []
        for _ in range(80):
            x = random.randrange(0, width)
            y = random.randrange(-height, 0)
            speed = random.uniform(50, 150)
            char = random.choice(string.ascii_letters + string.digits)
            self.rain_glyphs.append([x, y, speed, char])
        # Initialize list for score pop-up animations
        self.popups = []
        # Spawn the first piece(s) for each board
        self._spawn_piece(self.board1)
        if self.board2:
            # Default time limit 2 minutes (will adjust if another mode is selected)
            self.time_left = 120
            self._spawn_piece(self.board2)

    def _create_board(self, playfield_x):
        """Create a new board structure (grid and related stats)."""
        return {
            "playfield_x": playfield_x,
            "playfield_y": self.playfield_y,
            "grid": [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)],
            "score": 0,
            "drop_delay": 0.8,  # initial fall speed (seconds per drop)
            "drop_timer": 0,
            "next_piece": None,
            "current": None,
            "gameover": False,
            "viruses": set(),
        }

    def _init_viruses(self, board):
        """Randomly place initial viruses on the board."""
        # Decide number of viruses (fixed or based on mode). We'll use 15 for a balanced game.
        virus_count = 15
        # Place viruses in random positions, avoiding the top 3 rows to leave room for spawning pills
        rows_range = list(range(3, GRID_HEIGHT))
        cols_range = list(range(0, GRID_WIDTH))
        placed = 0
        while placed < virus_count:
            r = random.choice(rows_range)
            c = random.choice(cols_range)
            if board["grid"][r][c] is None:  # empty spot
                color = random.choice(COLORS)  # choose a random color for the virus
                board["grid"][r][c] = color
                board["viruses"].add((r, c))
                placed += 1

    def _random_piece(self):
        """Generate a new falling pill piece with two colored halves."""
        c1 = random.choice(COLORS)
        c2 = random.choice(COLORS)
        # Each piece is a domino of two blocks; start in horizontal orientation (rot=0)
        return {"rot": 0, "x": 0, "y": 0, "colors": [c1, c2]}

    def _spawn_piece(self, board):
        """Move the next piece into current and generate a new next piece."""
        piece = board["next_piece"]
        if piece is None:
            piece = self._random_piece()
        # Spawn at top center (horizontal orientation with left half at center column)
        piece["rot"] = 0
        piece["x"] = GRID_WIDTH // 2 - 1
        piece["y"] = 0
        board["current"] = piece
        # Prepare the next upcoming piece
        board["next_piece"] = self._random_piece()
        # Check for game over condition: if spawned piece collides immediately
        if self._collides(board, board["current"], dx=0, dy=0):
            board["gameover"] = True
            # End game if this is a single-player game or both players are blocked
            if self.num_players == 1 or (
                self.board1["gameover"] and (not self.board2 or self.board2["gameover"])
            ):
                self.state = "gameover"
                self.update_stats()

    def _collides(self, board, piece, dx=0, dy=0):
        """Check if moving the piece by (dx, dy) causes a collision (wall or block)."""
        # Define relative offsets for the two blocks based on orientation
        offsets = [(0, 0), (1, 0)] if piece["rot"] == 0 else [(0, 0), (0, 1)]
        for ox, oy in offsets:
            x = piece["x"] + ox + dx
            y = piece["y"] + oy + dy
            # Check boundaries
            if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
                return True
            # Check if cell is occupied by a placed block or virus
            if board["grid"][y][x] is not None:
                return True
        return False

    def _rotate_piece(self, board):
        """Attempt to rotate the current piece 90 degrees clockwise (if space allows)."""
        piece = board["current"]
        if not piece:
            return
        if piece["rot"] == 0:
            # Horizontal -> Vertical (pivot on left/top block)
            # Only rotate if within bounds and target cell below pivot is free
            if (
                piece["y"] < GRID_HEIGHT - 1
                and board["grid"][piece["y"] + 1][piece["x"]] is None
            ):
                piece["rot"] = 1
            # else: cannot rotate (bottom out of bounds or blocked)
        else:
            # Vertical -> Horizontal (pivot on top block)
            # Only rotate if within bounds and cell to the right of pivot is free
            if (
                piece["x"] < GRID_WIDTH - 1
                and board["grid"][piece["y"]][piece["x"] + 1] is None
            ):
                piece["rot"] = 0
            # else: cannot rotate (at right wall or blocked)

    def _lock_piece(self, board):
        """Lock the current falling piece into the grid (when it lands)."""
        piece = board["current"]
        if not piece:
            return
        # Determine the grid cells occupied by the piece's two halves
        offsets = [(0, 0), (1, 0)] if piece["rot"] == 0 else [(0, 0), (0, 1)]
        for idx, (ox, oy) in enumerate(offsets):
            x = piece["x"] + ox
            y = piece["y"] + oy
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                board["grid"][y][x] = piece["colors"][idx]
                # (If a virus was in this cell, it will be cleared in the matching step if matched)
        board["current"] = None

    def _clear_matches(self, board):
        """
        Clear any horizontal or vertical sequences of 4 or more same-colored blocks.
        Returns True if any blocks were cleared.
        """
        grid = board["grid"]
        rows, cols = GRID_HEIGHT, GRID_WIDTH
        to_clear = set()
        # Check horizontal sequences
        for r in range(rows):
            c = 0
            while c < cols:
                if grid[r][c] is not None:
                    color = grid[r][c]
                    length = 1
                    # count consecutive same-color cells in this row
                    while c + length < cols and grid[r][c + length] == color:
                        length += 1
                    if length >= 4:
                        for k in range(length):
                            to_clear.add((r, c + k))
                    c += length
                else:
                    c += 1
        # Check vertical sequences
        for c in range(cols):
            r = 0
            while r < rows:
                if grid[r][c] is not None:
                    color = grid[r][c]
                    length = 1
                    while r + length < rows and grid[r + length][c] == color:
                        length += 1
                    if length >= 4:
                        for k in range(length):
                            to_clear.add((r + k, c))
                    r += length
                else:
                    r += 1
        if not to_clear:
            return False  # no matches found
        # Remove matched cells and count viruses cleared
        viruses_cleared = 0
        for r, c in to_clear:
            if grid[r][c] is None:
                continue
            if (r, c) in board["viruses"]:
                board["viruses"].discard((r, c))  # remove cleared virus from set
                viruses_cleared += 1
            grid[r][c] = None
        # Update score for cleared blocks
        board["score"] += len(to_clear) * 100
        # Apply opponent penalty for viruses cleared
        if viruses_cleared > 0 and self.num_players == 2:
            other_board = self.board2 if board is self.board1 else self.board1
            deduction = viruses_cleared * 100
            other_board["score"] = max(0, other_board["score"] - deduction)
            # Create a popup for the opponent showing the score deduction
            opp_pf_x = other_board["playfield_x"]
            opp_pf_y = other_board["playfield_y"]
            popup_x = opp_pf_x + GRID_WIDTH * self.cell + 50
            popup_y = opp_pf_y + 50 + 120
            self.popups.append(
                {
                    "text": f"-{deduction}",
                    "x": popup_x,
                    "y": popup_y,
                    "color": (255, 0, 0),
                    "timer": 1.5,
                }
            )
        # Let any floating pieces fall down into cleared gaps
        self._apply_gravity(board)
        # Check for chain reactions (continue clearing as long as new matches form)
        while True:
            to_clear_again = set()
            # Repeat horizontal and vertical checks
            for r in range(rows):
                c = 0
                while c < cols:
                    if grid[r][c] is not None:
                        color = grid[r][c]
                        length = 1
                        while c + length < cols and grid[r][c + length] == color:
                            length += 1
                        if length >= 4:
                            for k in range(length):
                                to_clear_again.add((r, c + k))
                        c += length
                    else:
                        c += 1
            for c in range(cols):
                r = 0
                while r < rows:
                    if grid[r][c] is not None:
                        color = grid[r][c]
                        length = 1
                        while r + length < rows and grid[r + length][c] == color:
                            length += 1
                        if length >= 4:
                            for k in range(length):
                                to_clear_again.add((r + k, c))
                        r += length
                    else:
                        r += 1
            if not to_clear_again:
                break
            # Clear new matches
            viruses_cleared_again = 0
            for r, c in to_clear_again:
                if grid[r][c] is None:
                    continue
                if (r, c) in board["viruses"]:
                    board["viruses"].discard((r, c))
                    viruses_cleared_again += 1
                grid[r][c] = None
            board["score"] += len(to_clear_again) * 100
            if viruses_cleared_again > 0 and self.num_players == 2:
                other_board = self.board2 if board is self.board1 else self.board1
                deduction = viruses_cleared_again * 100
                other_board["score"] = max(0, other_board["score"] - deduction)
                popup_x = other_board["playfield_x"] + GRID_WIDTH * self.cell + 50
                popup_y = other_board["playfield_y"] + 50 + 120
                self.popups.append(
                    {
                        "text": f"-{deduction}",
                        "x": popup_x,
                        "y": popup_y,
                        "color": (255, 0, 0),
                        "timer": 1.5,
                    }
                )
            self._apply_gravity(board)
        return True

    def _apply_gravity(self, board):
        """After a clear, drop any remaining floating blocks down into empty spaces."""
        grid = board["grid"]
        # For each column, move blocks down to fill None gaps
        for c in range(GRID_WIDTH):
            for r in range(GRID_HEIGHT - 2, -1, -1):
                if grid[r][c] is not None and grid[r + 1][c] is None:
                    # Drop this block down until it lands
                    nr = r
                    while nr + 1 < GRID_HEIGHT and grid[nr + 1][c] is None:
                        grid[nr + 1][c] = grid[nr][c]
                        grid[nr][c] = None
                        nr += 1

    def handle_keyboard(self, event):
        # Handle keyboard input for different game states
        if self.state == "instructions":
            if event.type == pygame.KEYDOWN:
                if self.num_players == 2:
                    # In 2-player mode, wait for mode selection (1,2,3 keys)
                    if event.key in (pygame.K_1, pygame.K_KP1):
                        self.time_left = 60  # 1-minute Blitz
                        self.state = "play"
                    elif event.key in (pygame.K_2, pygame.K_KP2):
                        self.time_left = 120  # 2-minute Normal
                        self.state = "play"
                    elif event.key in (pygame.K_3, pygame.K_KP3):
                        self.time_left = 300  # 5-minute Long game
                        self.state = "play"
                    # Ignore other keys until a valid mode is chosen
                else:
                    # Single-player: any key to start
                    self.state = "play"
        elif self.state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    # Pause the game
                    self.state = "pause"
                    self.pause_index = 0
                # Player 1 controls (arrows + space)
                if not self.board1["gameover"]:
                    if event.key == pygame.K_LEFT and not self._collides(
                        self.board1, self.board1["current"], dx=-1, dy=0
                    ):
                        self.board1["current"]["x"] -= 1
                    elif event.key == pygame.K_RIGHT and not self._collides(
                        self.board1, self.board1["current"], dx=1, dy=0
                    ):
                        self.board1["current"]["x"] += 1
                    elif event.key == pygame.K_DOWN and not self._collides(
                        self.board1, self.board1["current"], dx=0, dy=1
                    ):
                        self.board1["current"]["y"] += 1  # soft drop
                    elif event.key == pygame.K_UP:
                        self._rotate_piece(self.board1)
                    elif event.key == pygame.K_SPACE:
                        # Hard drop: move down until collision
                        while not self._collides(
                            self.board1, self.board1["current"], dx=0, dy=1
                        ):
                            self.board1["current"]["y"] += 1
                # Player 2 controls (WASD + F) if in 2-player mode
                if (
                    self.num_players == 2
                    and self.board2
                    and not self.board2["gameover"]
                ):
                    if event.key == pygame.K_a and not self._collides(
                        self.board2, self.board2["current"], dx=-1, dy=0
                    ):
                        self.board2["current"]["x"] -= 1
                    elif event.key == pygame.K_d and not self._collides(
                        self.board2, self.board2["current"], dx=1, dy=0
                    ):
                        self.board2["current"]["x"] += 1
                    elif event.key == pygame.K_s and not self._collides(
                        self.board2, self.board2["current"], dx=0, dy=1
                    ):
                        self.board2["current"]["y"] += 1
                    elif event.key == pygame.K_w:
                        self._rotate_piece(self.board2)
                    elif event.key == pygame.K_f:
                        while not self._collides(
                            self.board2, self.board2["current"], dx=0, dy=1
                        ):
                            self.board2["current"]["y"] += 1
        elif self.state == "pause":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    # Navigate pause menu up
                    self.pause_index = (self.pause_index - 1) % len(self.pause_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    # Navigate pause menu down
                    self.pause_index = (self.pause_index + 1) % len(self.pause_options)
                elif event.key == pygame.K_RETURN:
                    # Activate selected pause menu option
                    choice = self.pause_options[self.pause_index]
                    if choice == "Resume":
                        self.state = "play"
                    elif choice == "Quit":
                        self.update_stats()
                        self.done = True
                        self.next = "menu"
                    elif choice == "Fullscreen":
                        pygame.display.toggle_fullscreen()
                        self.settings["fullscreen"] = not self.settings.get(
                            "fullscreen", False
                        )
                        save_json(SETTINGS_PATH, self.settings)
                    elif choice == "Volume +":
                        # Increase volume
                        vol = min(1.0, self.settings.get("sound_volume", 1.0) + 0.1)
                        self.settings["sound_volume"] = round(vol, 2)
                        pygame.mixer.music.set_volume(vol)
                        save_json(SETTINGS_PATH, self.settings)
                    elif choice == "Volume -":
                        # Decrease volume
                        vol = max(0.0, self.settings.get("sound_volume", 1.0) - 0.1)
                        self.settings["sound_volume"] = round(vol, 2)
                        pygame.mixer.music.set_volume(vol)
                        save_json(SETTINGS_PATH, self.settings)
                elif event.key == pygame.K_ESCAPE:
                    # Unpause
                    self.state = "play"
        elif self.state == "gameover":
            if event.type == pygame.KEYDOWN:
                # Any key press on Game Over screen returns to menu
                self.done = True
                self.next = "menu"

    def handle_gamepad(self, event):
        # Allow gamepad control (primarily for player 1)
        if self.state == "instructions":
            if event.type == pygame.JOYBUTTONDOWN:
                if self.num_players == 2:
                    # Default to Normal (2 min) if using gamepad to start
                    self.time_left = 120
                self.state = "play"
        elif self.state == "play":
            # Map gamepad buttons similar to keyboard for P1
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # A button -> rotate P1
                    self._rotate_piece(self.board1)
                elif event.button == 1:  # B button -> hard drop P1
                    while not self._collides(
                        self.board1, self.board1["current"], dx=0, dy=1
                    ):
                        self.board1["current"]["y"] += 1
                elif event.button in (7, 9):  # Start/Select -> pause
                    self.state = "pause"
                    self.pause_index = 0
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:  # left stick horizontal
                    if event.value < -0.5 and not self._collides(
                        self.board1, self.board1["current"], dx=-1, dy=0
                    ):
                        self.board1["current"]["x"] -= 1
                    elif event.value > 0.5 and not self._collides(
                        self.board1, self.board1["current"], dx=1, dy=0
                    ):
                        self.board1["current"]["x"] += 1
                elif event.axis == 1:  # left stick vertical
                    if event.value > 0.5 and not self._collides(
                        self.board1, self.board1["current"], dx=0, dy=1
                    ):
                        self.board1["current"]["y"] += 1
            elif event.type == pygame.JOYHATMOTION:
                x, y = event.value  # D-pad
                if x == -1 and not self._collides(
                    self.board1, self.board1["current"], dx=-1, dy=0
                ):
                    self.board1["current"]["x"] -= 1
                elif x == 1 and not self._collides(
                    self.board1, self.board1["current"], dx=1, dy=0
                ):
                    self.board1["current"]["x"] += 1
                if y == -1 and not self._collides(
                    self.board1, self.board1["current"], dx=0, dy=1
                ):
                    self.board1["current"]["y"] += 1
                elif y == 1:
                    self._rotate_piece(self.board1)
        elif self.state == "pause":
            # Navigate pause menu with gamepad (D-pad or left stick, A to select, B/Start to cancel)
            if event.type in (pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                if event.type == pygame.JOYHATMOTION:
                    _, hat_y = event.value
                    vert = -hat_y
                else:
                    if event.axis != 1:
                        return
                    vert = event.value
                if vert < -0.5 or vert == -1:
                    self.pause_index = (self.pause_index - 1) % len(self.pause_options)
                elif vert > 0.5 or vert == 1:
                    self.pause_index = (self.pause_index + 1) % len(self.pause_options)
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # A button to select
                    choice = self.pause_options[self.pause_index]
                    if choice == "Resume":
                        self.state = "play"
                    elif choice == "Quit":
                        self.update_stats()
                        self.done = True
                        self.next = "menu"
                    elif choice == "Fullscreen":
                        pygame.display.toggle_fullscreen()
                        self.settings["fullscreen"] = not self.settings.get(
                            "fullscreen", False
                        )
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
                elif event.button in (
                    1,
                    7,
                    9,
                ):  # B or Start/Select to resume without change
                    self.state = "play"
        elif self.state == "gameover":
            if event.type == pygame.JOYBUTTONDOWN:
                self.done = True
                self.next = "menu"

    def update(self, dt):
        # Only progress game logic in "play" state
        if self.state != "play":
            if self.state == "pause":
                # Continuously apply volume changes while paused
                pygame.mixer.music.set_volume(self.settings.get("sound_volume", 1.0))
            return
        # Update falling code background positions
        width, height = self.screen.get_size()
        for glyph in self.rain_glyphs:
            glyph[1] += glyph[2] * dt
            if glyph[1] > height:
                glyph[0] = random.randrange(0, width)
                glyph[1] = random.randrange(-height, 0)
                glyph[2] = random.uniform(50, 150)
                glyph[3] = random.choice(string.ascii_letters + string.digits)
        # Game piece falling and locking
        boards = [self.board1]
        if self.board2:
            boards.append(self.board2)
        for board in boards:
            if board["gameover"]:
                continue
            board["drop_timer"] += dt
            if board["drop_timer"] >= board["drop_delay"]:
                board["drop_timer"] = 0
                # Try to move piece down
                if not self._collides(board, board["current"], dx=0, dy=1):
                    board["current"]["y"] += 1
                else:
                    # Piece landed – lock it and clear matches
                    self._lock_piece(board)
                    self._clear_matches(board)
                    # If single-player and all viruses cleared, trigger win
                    if self.num_players == 1 and len(board["viruses"]) == 0:
                        self.state = "gameover"
                        self.win = True
                        self.update_stats()
                    # Spawn a new piece if game continues
                    if not board["gameover"] and self.state == "play":
                        self._spawn_piece(board)
        # Update display scores for convenience
        self.score = self.board1["score"]
        if self.board2:
            self.score2 = self.board2["score"]
        # Decrease timer in 2-player mode and end game when time is up
        if self.num_players == 2:
            self.time_left -= dt
            if self.time_left <= 0:
                self.time_left = 0
                # Time's up – end the round
                self.state = "gameover"
                self.time_up = True
                self.update_stats()
        # Update popup animations (score penalties)
        for popup in list(self.popups):
            popup["y"] += 50 * dt  # drop the popup text downward
            popup["timer"] -= dt
            if popup["timer"] <= 0:
                self.popups.remove(popup)

    def draw(self):
        # Fill background
        self.screen.fill(self.bg_color)
        width, height = self.screen.get_size()
        # Draw falling "rain" glyphs in background
        for x, y, _, char in self.rain_glyphs:
            glyph_surface = self.rain_font.render(char, True, self.normal_color)
            self.screen.blit(glyph_surface, (x, y))
        # Draw each playfield (one or two)
        boards = [self.board1] if not self.board2 else [self.board1, self.board2]
        for idx, board in enumerate(boards):
            # Draw playfield grid border
            px = board["playfield_x"]
            py = board["playfield_y"]
            playfield_rect = pygame.Rect(
                px - 4, py - 4, GRID_WIDTH * self.cell + 8, GRID_HEIGHT * self.cell + 8
            )
            pygame.draw.rect(self.screen, self.normal_color, playfield_rect, 2)
            # Draw placed blocks and viruses
            for r in range(GRID_HEIGHT):
                for c in range(GRID_WIDTH):
                    color = board["grid"][r][c]
                    if color:
                        rect = pygame.Rect(
                            px + c * self.cell, py + r * self.cell, self.cell, self.cell
                        )
                        pygame.draw.rect(self.screen, color, rect)
                        pygame.draw.rect(self.screen, self.normal_color, rect, 1)
            # Draw current falling piece (if game not over on that board)
            if (
                self.state in ("play", "pause")
                and not board["gameover"]
                and board["current"]
            ):
                piece = board["current"]
                offsets = [(0, 0), (1, 0)] if piece["rot"] == 0 else [(0, 0), (0, 1)]
                for idx2, (ox, oy) in enumerate(offsets):
                    cx = piece["x"] + ox
                    cy = piece["y"] + oy
                    rect = pygame.Rect(
                        px + cx * self.cell, py + cy * self.cell, self.cell, self.cell
                    )
                    pygame.draw.rect(self.screen, piece["colors"][idx2], rect)
                    pygame.draw.rect(self.screen, self.normal_color, rect, 1)
            # Draw next piece preview box and piece
            preview_x = px + GRID_WIDTH * self.cell + 50
            preview_y = py + 50
            preview_rect = pygame.Rect(preview_x - 10, preview_y - 10, 100, 100)
            pygame.draw.rect(self.screen, self.normal_color, preview_rect, 2)
            next_piece = board["next_piece"]
            if next_piece:
                # Always draw preview in horizontal orientation
                for j, color in enumerate(next_piece["colors"]):
                    rect = pygame.Rect(
                        preview_x + j * self.cell, preview_y, self.cell, self.cell
                    )
                    pygame.draw.rect(self.screen, color, rect)
                    pygame.draw.rect(self.screen, self.normal_color, rect, 1)
            # Draw score labels
            if self.board2:
                score_label = f"P{idx+1}: {board['score']}"
            else:
                score_label = f"Score: {board['score']}"
            score_surf = self.font.render(score_label, True, self.highlight_color)
            self.screen.blit(score_surf, (preview_x, preview_y + 120))
            if idx == 0:
                # Player 1 side: show high score
                hs_surf = self.font.render(
                    f"High: {self.high_score}", True, self.highlight_color
                )
                self.screen.blit(hs_surf, (preview_x, preview_y + 150))
        # Draw any floating score popups
        for popup in self.popups:
            pop_surf = self.font.render(popup["text"], True, popup["color"])
            self.screen.blit(pop_surf, (popup["x"], popup["y"]))
        # Draw overlay screens for instructions, pause, and game over states
        if self.state == "instructions":
            # Title
            title_text = self.big_font.render("VIRUS", True, self.highlight_color)
            title_rect = title_text.get_rect(center=(width // 2, height // 5))
            self.screen.blit(title_text, title_rect)
            if self.board2:
                # 2-player: prompt mode selection
                info_text = self.font.render(
                    "P1: Arrows   P2: WASD", True, self.highlight_color
                )
                mode_text = self.font.render(
                    "Press 1 (Blitz), 2 (Normal), or 3 (Long)",
                    True,
                    self.highlight_color,
                )
                rect2 = info_text.get_rect(center=(width // 2, height // 2))
                rect3 = mode_text.get_rect(center=(width // 2, height // 2 + 40))
                self.screen.blit(info_text, rect2)
                self.screen.blit(mode_text, rect3)
            else:
                info_text = self.font.render(
                    "Press any key to start", True, self.highlight_color
                )
                rect = info_text.get_rect(center=(width // 2, height // 2))
                self.screen.blit(info_text, rect)
        elif self.state == "pause":
            # Translucent overlay
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            # Pause menu options
            for i, option in enumerate(self.pause_options):
                color = (
                    self.highlight_color if i == self.pause_index else self.normal_color
                )
                prefix = "> " if i == self.pause_index else "  "
                option_surf = self.big_font.render(prefix + option, True, color)
                opt_rect = option_surf.get_rect(
                    center=(width // 2, height // 3 + i * 40)
                )
                self.screen.blit(option_surf, opt_rect)
        elif self.state == "gameover":
            # Darken screen
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            if self.num_players == 2:
                # Show "TIME UP" if ended by timer, otherwise "GAME OVER"
                title = "TIME UP" if getattr(self, "time_up", False) else "GAME OVER"
                result_text = ""
                if self.score > self.score2:
                    result_text = "P1 WINS!"
                elif self.score2 > self.score:
                    result_text = "P2 WINS!"
                else:
                    result_text = "TIE GAME!"
                text1 = self.big_font.render(title, True, self.highlight_color)
                text2 = self.big_font.render(result_text, True, self.highlight_color)
                text3 = self.font.render("Press any key", True, self.highlight_color)
                rect1 = text1.get_rect(center=(width // 2, height // 3))
                rect2 = text2.get_rect(center=(width // 2, height // 2))
                rect3 = text3.get_rect(center=(width // 2, height // 2 + 40))
                self.screen.blit(text1, rect1)
                self.screen.blit(text2, rect2)
                self.screen.blit(text3, rect3)
            else:
                # Single-player: either win (cleared all viruses) or game over (topped out)
                if getattr(self, "win", False):
                    text_main = "YOU WIN!"
                else:
                    text_main = "GAME OVER"
                text1 = self.big_font.render(text_main, True, self.highlight_color)
                text2 = self.font.render("Press any key", True, self.highlight_color)
                rect1 = text1.get_rect(center=(width // 2, height // 3))
                rect2 = text2.get_rect(center=(width // 2, height // 2))
                self.screen.blit(text1, rect1)
                self.screen.blit(text2, rect2)

    def update_stats(self):
        """Update high score data and play count at end of a game session."""
        best_score = self.board1["score"]
        if self.board2:
            best_score = max(best_score, self.board2["score"])
        if best_score > self.high_score:
            self.high_score = best_score
        # Record stats
        self.hs_data["highscore"] = self.high_score
        self.hs_data["plays"] = self.hs_data.get("plays", 0) + 1
        self.hs_data["last_played"] = datetime.now().isoformat()
        save_json(HS_PATH, self.hs_data)
