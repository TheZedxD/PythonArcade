from typing import List, Set, Tuple

import pygame

from state import State
from utils.persistence import load_json, save_json
from utils.resources import asset_path, save_path

SETTINGS_PATH = save_path("settings.json")

GRID_SIZE = 20
NUM_SEGMENTS = 12
MOVE_DELAY = 0.2


class WyrmGame(State):
    """Minimal Centipede-style game."""

    def __init__(self) -> None:
        super().__init__()
        self.score1 = 0
        self.score2 = 0
        self.lives1 = 3
        self.lives2 = 3
        self.wyrms: List[List[Tuple[int, int]]] = [
            [(i, 0) for i in range(NUM_SEGMENTS)]
        ]
        self.blocks: Set[Tuple[int, int]] = set()
        self.move_timer = 0.0
        self.move_delay = MOVE_DELAY
        self.direction = 1
        self.start_pos1 = [0, 0]
        self.start_pos2 = [0, 0]
        self.player1 = self.start_pos1.copy()
        self.player2 = self.start_pos2.copy()
        self.bullets: List[List[int]] = []  # [x, y, player]
        self.segment_img: pygame.Surface | None = None
        self.shot_sound: pygame.mixer.Sound | None = None
        self.grid_w = 0
        self.grid_h = 0
        self.font: pygame.font.Font | None = None
        self.big_font: pygame.font.Font | None = None
        self.overlay: pygame.Surface | None = None
        self.state = "play"
        self.pause_options = [
            "Resume",
            "Volume -",
            "Volume +",
            "Fullscreen",
            "Quit",
        ]
        self.pause_index = 0
        self.settings: dict = {}

    def startup(self, screen: pygame.Surface, num_players: int = 1) -> None:
        super().startup(screen, num_players)
        width, height = self.screen.get_size()
        self.grid_w = width // GRID_SIZE
        self.grid_h = height // GRID_SIZE
        start_row = int(self.grid_h * 0.8)
        self.start_pos1 = [int(self.grid_w * 0.4), start_row]
        self.start_pos2 = [int(self.grid_w * 0.6), start_row]
        self.player1 = self.start_pos1.copy()
        self.player2 = self.start_pos2.copy()
        self.score1 = 0
        self.score2 = 0
        self.lives1 = 3
        self.lives2 = 3
        self.move_delay = MOVE_DELAY
        self.font = pygame.font.SysFont("Courier", 20)
        self.big_font = pygame.font.SysFont("Courier", 32)
        try:
            self.segment_img = pygame.image.load(
                asset_path("games", "wyrm", "assets", "segment.png")
            ).convert_alpha()
        except Exception:
            self.segment_img = None
        try:
            self.shot_sound = pygame.mixer.Sound(
                asset_path("games", "wyrm", "assets", "shot.wav")
            )
        except Exception:
            self.shot_sound = None
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
        self.overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.state = "play"
        self.pause_index = 0

    def handle_keyboard(self, event: pygame.event.Event) -> None:
        if self.state == "pause":
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
                elif event.key == pygame.K_ESCAPE:
                    self.state = "play"
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = "pause"
                self.pause_index = 0
                return

            # Player 1 controls (arrows + space)
            if event.key == pygame.K_LEFT:
                self.player1[0] = max(0, self.player1[0] - 1)
            elif event.key == pygame.K_RIGHT:
                self.player1[0] = min(self.grid_w - 1, self.player1[0] + 1)
            elif event.key == pygame.K_UP:
                min_row = int(self.grid_h * 0.8)
                self.player1[1] = max(min_row, self.player1[1] - 1)
            elif event.key == pygame.K_DOWN:
                self.player1[1] = min(self.grid_h - 1, self.player1[1] + 1)
            elif event.key == pygame.K_SPACE:
                self.bullets.append([self.player1[0], self.player1[1] - 1, 1])
                if self.shot_sound:
                    self.shot_sound.play()

            # Player 2 controls (WASD + left ctrl)
            if self.num_players > 1:
                if event.key == pygame.K_a:
                    self.player2[0] = max(0, self.player2[0] - 1)
                elif event.key == pygame.K_d:
                    self.player2[0] = min(self.grid_w - 1, self.player2[0] + 1)
                elif event.key == pygame.K_w:
                    min_row = int(self.grid_h * 0.8)
                    self.player2[1] = max(min_row, self.player2[1] - 1)
                elif event.key == pygame.K_s:
                    self.player2[1] = min(self.grid_h - 1, self.player2[1] + 1)
                elif event.key == pygame.K_LCTRL:
                    self.bullets.append([self.player2[0], self.player2[1] - 1, 2])
                    if self.shot_sound:
                        self.shot_sound.play()

    def handle_gamepad(self, event: pygame.event.Event) -> None:
        if self.state == "pause":
            if event.type in (pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
                if event.type == pygame.JOYHATMOTION:
                    _, y = event.value
                    vert = -y
                else:
                    if event.axis != 1:
                        return
                    vert = event.value
                if vert < -0.5 or vert == -1:
                    self.pause_index = (self.pause_index - 1) % len(self.pause_options)
                elif vert > 0.5 or vert == 1:
                    self.pause_index = (self.pause_index + 1) % len(self.pause_options)
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    choice = self.pause_options[self.pause_index]
                    if choice == "Resume":
                        self.state = "play"
                    elif choice == "Quit":
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
                elif event.button in (1, 7, 9):
                    self.state = "play"
            return

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 7:
                self.state = "pause"
                self.pause_index = 0
            elif event.button == 0:
                self.bullets.append([self.player1[0], self.player1[1] - 1, 1])
                if self.shot_sound:
                    self.shot_sound.play()
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value < -0.5:
                    self.player1[0] = max(0, self.player1[0] - 1)
                elif event.value > 0.5:
                    self.player1[0] = min(self.grid_w - 1, self.player1[0] + 1)
            elif event.axis == 1:
                min_row = int(self.grid_h * 0.8)
                if event.value < -0.5:
                    self.player1[1] = max(min_row, self.player1[1] - 1)
                elif event.value > 0.5:
                    self.player1[1] = min(self.grid_h - 1, self.player1[1] + 1)
        elif event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if x == -1:
                self.player1[0] = max(0, self.player1[0] - 1)
            elif x == 1:
                self.player1[0] = min(self.grid_w - 1, self.player1[0] + 1)
            min_row = int(self.grid_h * 0.8)
            if y == 1:
                self.player1[1] = max(min_row, self.player1[1] - 1)
            elif y == -1:
                self.player1[1] = min(self.grid_h - 1, self.player1[1] + 1)

    def update(self, dt: float) -> None:
        if self.state != "play":
            if self.state == "pause":
                pygame.mixer.music.set_volume(self.settings.get("sound_volume", 1.0))
            return

        self.move_timer += dt
        if self.move_timer >= self.move_delay:
            self.move_timer = 0.0
            self._move_wyrms()

        for bullet in list(self.bullets):
            bullet[1] -= 1
            if bullet[1] < 0:
                self.bullets.remove(bullet)
                continue
            for ci, chain in enumerate(self.wyrms):
                for si, seg in enumerate(chain):
                    if (bullet[0], bullet[1]) == seg:
                        shooter = bullet[2]
                        self.bullets.remove(bullet)
                        self.handle_segment_hit(ci, si, shooter)
                        break

        # Check for collisions between players and wyrm segments
        for chain in self.wyrms:
            for seg in chain:
                if self.lives1 > 0 and tuple(self.player1) == seg:
                    self._player_hit(1)
                if (
                    self.num_players > 1
                    and self.lives2 > 0
                    and tuple(self.player2) == seg
                ):
                    self._player_hit(2)

    def _move_wyrms(self) -> None:
        for chain in self.wyrms:
            head_x, head_y = chain[0]
            new_x = head_x + self.direction
            if new_x < 0 or new_x >= self.grid_w or (new_x, head_y) in self.blocks:
                self.direction *= -1
                head_y += 1
                new_x = head_x + self.direction
            chain.insert(0, (new_x, head_y))
            chain.pop()

    def handle_segment_hit(
        self, chain_idx: int, seg_idx: int, shooter: int = 1
    ) -> None:
        chain = self.wyrms[chain_idx]
        hit_pos = chain[seg_idx]
        if seg_idx == 0:
            if shooter == 1:
                self.score1 += 100
            else:
                self.score2 += 100
            del chain[0]
            if not chain:
                del self.wyrms[chain_idx]
        else:
            if shooter == 1:
                self.score1 += 10
            else:
                self.score2 += 10
            left = chain[:seg_idx]
            right = chain[seg_idx + 1 :]
            self.blocks.add(hit_pos)
            self.wyrms[chain_idx] = left
            if right:
                self.wyrms.insert(chain_idx + 1, right)
        self._update_speed()

    def _player_hit(self, player: int) -> None:
        if player == 1:
            self.lives1 -= 1
            if self.lives1 <= 0 and (self.num_players == 1 or self.lives2 <= 0):
                self.done = True
                self.next = "menu"
            elif self.lives1 > 0:
                self.player1 = self.start_pos1.copy()
        else:
            self.lives2 -= 1
            if self.lives2 <= 0 and self.lives1 <= 0:
                self.done = True
                self.next = "menu"
            elif self.lives2 > 0:
                self.player2 = self.start_pos2.copy()

    def _update_speed(self) -> None:
        total = self.score1 + self.score2
        level = total // 500
        self.move_delay = max(0.05, MOVE_DELAY * (0.9**level))

    def draw(self) -> None:
        self.screen.fill((0, 0, 0))
        for chain in self.wyrms:
            for x, y in chain:
                rect = pygame.Rect(x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
                if self.segment_img:
                    self.screen.blit(self.segment_img, rect)
                else:
                    pygame.draw.rect(self.screen, (0, 255, 0), rect)
        for x, y in self.blocks:
            pygame.draw.rect(
                self.screen,
                (155, 0, 155),
                (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE),
            )
        if self.lives1 > 0:
            px, py = self.player1
            pygame.draw.rect(
                self.screen,
                (0, 255, 0),
                (px * GRID_SIZE, py * GRID_SIZE, GRID_SIZE, GRID_SIZE),
            )
        if self.num_players > 1 and self.lives2 > 0:
            px, py = self.player2
            pygame.draw.rect(
                self.screen,
                (0, 128, 255),
                (px * GRID_SIZE, py * GRID_SIZE, GRID_SIZE, GRID_SIZE),
            )
        for x, y, shooter in self.bullets:
            color = (0, 255, 0) if shooter == 1 else (0, 128, 255)
            pygame.draw.rect(
                self.screen,
                color,
                (
                    x * GRID_SIZE + GRID_SIZE // 4,
                    y * GRID_SIZE,
                    GRID_SIZE // 2,
                    GRID_SIZE // 2,
                ),
            )
        if self.font:
            text = self.font.render(
                f"P1: {self.score1} L{self.lives1}", True, (0, 255, 0)
            )
            self.screen.blit(text, (5, 5))
            if self.num_players > 1:
                text2 = self.font.render(
                    f"P2: {self.score2} L{self.lives2}", True, (0, 255, 0)
                )
                self.screen.blit(
                    text2,
                    (self.screen.get_width() - text2.get_width() - 5, 5),
                )
        if self.state == "pause" and self.overlay and self.big_font:
            self.overlay.fill((0, 0, 0, 200))
            self.screen.blit(self.overlay, (0, 0))
            for i, option in enumerate(self.pause_options):
                color = (0, 255, 0) if i == self.pause_index else (0, 155, 0)
                prefix = "> " if i == self.pause_index else "  "
                text = self.big_font.render(prefix + option, True, color)
                rect = text.get_rect(
                    center=(
                        self.screen.get_width() // 2,
                        self.screen.get_height() // 2 + i * 40,
                    )
                )
                self.screen.blit(text, rect)

    def game_over(self, name: str) -> None:
        from high_scores import save_score

        save_score("wyrm", name, max(self.score1, self.score2))


def main() -> None:
    """Standalone entry point."""
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    game = WyrmGame()
    game.startup(screen)
    clock = pygame.time.Clock()
    running = True
    while running and not game.done:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.get_event(event)
        game.update(dt)
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
