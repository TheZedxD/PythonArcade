import pygame
from state import State
from .engine.track import create_demo_track
from .engine.renderer import Renderer
from .engine.physics import Car, Ghost


class KartGame(State):
    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        self.track = create_demo_track()
        self.player = Car(self.track)
        self.ghost = Ghost(self.track)
        self.renderer = Renderer(screen, self.track)
        self.font = pygame.font.SysFont("Courier", 20)
        self.lap = 0
        self.hud_color = (0, 255, 0)

    def handle_keyboard(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.done = True
            self.next = "menu"

    def update(self, dt):
        keys = pygame.key.get_pressed()
        controls = {
            'accelerate': keys[pygame.K_w],
            'brake': keys[pygame.K_s],
            'left': keys[pygame.K_a],
            'right': keys[pygame.K_d],
        }
        boost = keys[pygame.K_LSHIFT]
        prev_z = self.player.z
        self.player.update(dt, controls, boost)
        self.ghost.update(dt, self.player.z)
        if prev_z > self.player.z:
            self.lap += 1

    def draw(self):
        self.screen.fill((0, 0, 0))
        self.renderer.render(self.player, [self.ghost])
        lap_text = self.font.render(f"LAP {self.lap + 1}", True, self.hud_color)
        self.screen.blit(lap_text, (10, 10))
        speed_text = self.font.render(f"{int(self.player.speed)}", True, self.hud_color)
        self.screen.blit(speed_text, (10, 40))


# expose Game class for loader
Game = KartGame
