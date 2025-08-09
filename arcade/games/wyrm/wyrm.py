import os
from typing import List, Set, Tuple

import pygame

from state import State

GRID_SIZE = 20
NUM_SEGMENTS = 12
MOVE_DELAY = 0.2


class WyrmGame(State):
    """Minimal Centipede-style game."""

    def __init__(self) -> None:
        super().__init__()
        self.score = 0
        self.lives = 3
        self.wyrms: List[List[Tuple[int, int]]] = [
            [(i, 0) for i in range(NUM_SEGMENTS)]
        ]
        self.blocks: Set[Tuple[int, int]] = set()
        self.move_timer = 0.0
        self.direction = 1
        self.player = [0, 0]
        self.bullets: List[List[int]] = []
        self.segment_img: pygame.Surface | None = None
        self.shot_sound: pygame.mixer.Sound | None = None
        self.grid_w = 0
        self.grid_h = 0
        self.font: pygame.font.Font | None = None

    def startup(self, screen: pygame.Surface, num_players: int = 1) -> None:
        super().startup(screen, num_players)
        width, height = self.screen.get_size()
        self.grid_w = width // GRID_SIZE
        self.grid_h = height // GRID_SIZE
        self.player = [self.grid_w // 2, int(self.grid_h * 0.8)]
        self.font = pygame.font.SysFont("Courier", 20)
        base = os.path.join(os.path.dirname(__file__), "assets")
        try:
            self.segment_img = pygame.image.load(
                os.path.join(base, "segment.png")
            ).convert_alpha()
        except Exception:
            self.segment_img = None
        try:
            self.shot_sound = pygame.mixer.Sound(os.path.join(base, "shot.wav"))
        except Exception:
            self.shot_sound = None

    def handle_keyboard(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.done = True
                self.next = "menu"
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                self.player[0] = max(0, self.player[0] - 1)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                self.player[0] = min(self.grid_w - 1, self.player[0] + 1)
            elif event.key in (pygame.K_UP, pygame.K_w):
                min_row = int(self.grid_h * 0.8)
                self.player[1] = max(min_row, self.player[1] - 1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.player[1] = min(self.grid_h - 1, self.player[1] + 1)
            elif event.key == pygame.K_SPACE:
                self.bullets.append([self.player[0], self.player[1] - 1])
                if self.shot_sound:
                    self.shot_sound.play()

    def handle_gamepad(self, event: pygame.event.Event) -> None:
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == 7:
                self.done = True
                self.next = "menu"
            elif event.button == 0:
                self.bullets.append([self.player[0], self.player[1] - 1])
                if self.shot_sound:
                    self.shot_sound.play()
        elif event.type == pygame.JOYAXISMOTION:
            if event.axis == 0:
                if event.value < -0.5:
                    self.player[0] = max(0, self.player[0] - 1)
                elif event.value > 0.5:
                    self.player[0] = min(self.grid_w - 1, self.player[0] + 1)
            elif event.axis == 1:
                min_row = int(self.grid_h * 0.8)
                if event.value < -0.5:
                    self.player[1] = max(min_row, self.player[1] - 1)
                elif event.value > 0.5:
                    self.player[1] = min(self.grid_h - 1, self.player[1] + 1)
        elif event.type == pygame.JOYHATMOTION:
            x, y = event.value
            if x == -1:
                self.player[0] = max(0, self.player[0] - 1)
            elif x == 1:
                self.player[0] = min(self.grid_w - 1, self.player[0] + 1)
            min_row = int(self.grid_h * 0.8)
            if y == 1:
                self.player[1] = max(min_row, self.player[1] - 1)
            elif y == -1:
                self.player[1] = min(self.grid_h - 1, self.player[1] + 1)

    def update(self, dt: float) -> None:
        self.move_timer += dt
        if self.move_timer >= MOVE_DELAY:
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
                        self.bullets.remove(bullet)
                        self.handle_segment_hit(ci, si)
                        break

    def _move_wyrms(self) -> None:
        for chain in self.wyrms:
            head_x, head_y = chain[0]
            new_x = head_x + self.direction
            if (
                new_x < 0
                or new_x >= self.grid_w
                or (new_x, head_y) in self.blocks
            ):
                self.direction *= -1
                head_y += 1
                new_x = head_x + self.direction
            chain.insert(0, (new_x, head_y))
            chain.pop()

    def handle_segment_hit(self, chain_idx: int, seg_idx: int) -> None:
        chain = self.wyrms[chain_idx]
        hit_pos = chain[seg_idx]
        if seg_idx == 0:
            self.score += 100
            del chain[0]
            if not chain:
                del self.wyrms[chain_idx]
        else:
            self.score += 10
            left = chain[:seg_idx]
            right = chain[seg_idx + 1 :]
            self.blocks.add(hit_pos)
            self.wyrms[chain_idx] = left
            if right:
                self.wyrms.insert(chain_idx + 1, right)

    def draw(self) -> None:
        self.screen.fill((0, 0, 0))
        for chain in self.wyrms:
            for x, y in chain:
                rect = pygame.Rect(
                    x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE
                )
                if self.segment_img:
                    self.screen.blit(self.segment_img, rect)
                else:
                    pygame.draw.rect(self.screen, (0, 255, 0), rect)
        for x, y in self.blocks:
            pygame.draw.rect(
                self.screen, (0, 155, 0), (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            )
        px, py = self.player
        pygame.draw.rect(
            self.screen,
            (0, 255, 0),
            (px * GRID_SIZE, py * GRID_SIZE, GRID_SIZE, GRID_SIZE),
        )
        for x, y in self.bullets:
            pygame.draw.rect(
                self.screen,
                (0, 255, 0),
                (x * GRID_SIZE + GRID_SIZE // 4, y * GRID_SIZE, GRID_SIZE // 2, GRID_SIZE // 2),
            )
        if self.font:
            text = self.font.render(f"Score: {self.score}", True, (0, 255, 0))
            self.screen.blit(text, (5, 5))

    def game_over(self, name: str) -> None:
        from arcade.high_scores import save_score

        save_score("wyrm", name, self.score)


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
