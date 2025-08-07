import pygame
from state import State

class PlaceholderGameState(State):
    def startup(self, screen):
        super().startup(screen)
        self.font = pygame.font.SysFont("Courier", 36)

    def handle_keyboard(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.done = True
            self.next = "menu"

    def update(self, dt):
        pass

    def draw(self):
        self.screen.fill((0, 0, 0))
        text = self.font.render("WORK IN PROGRESS", True, (0, 255, 0))
        rect = text.get_rect(center=(self.screen.get_width() // 2,
                                     self.screen.get_height() // 2))
        self.screen.blit(text, rect)
