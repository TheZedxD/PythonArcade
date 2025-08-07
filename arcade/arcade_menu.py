import os
import pygame
from state import State

class MainMenuState(State):
    def __init__(self):
        super().__init__()
        self.options = []
        self.index = 0
        self.font = None
        self.normal_color = (0, 155, 0)
        self.highlight_color = (0, 255, 0)
        self.bg_color = (0, 0, 0)

    def startup(self, screen):
        super().startup(screen)
        self.font = pygame.font.SysFont("Courier", 32)
        base_dir = os.path.join(os.path.dirname(__file__), "games")
        self.options = [name for name in sorted(os.listdir(base_dir))
                        if os.path.isdir(os.path.join(base_dir, name))]
        self.options.append("Quit")
        self.index = 0

    def get_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit = True
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % len(self.options)
            elif event.key in (pygame.K_UP, pygame.K_w):
                self.index = (self.index - 1) % len(self.options)
            elif event.key == pygame.K_RETURN:
                choice = self.options[self.index]
                if choice == "Quit":
                    self.quit = True
                else:
                    self.next = choice
                    self.done = True

    def update(self, dt):
        pass

    def draw(self):
        self.screen.fill(self.bg_color)
        width, height = self.screen.get_size()
        for i, option in enumerate(self.options):
            color = self.highlight_color if i == self.index else self.normal_color
            text = self.font.render(option, True, color)
            rect = text.get_rect(center=(width // 2, height // 3 + i * 40))
            if i == self.index:
                highlight_rect = rect.inflate(20, 10)
                pygame.draw.rect(self.screen, self.highlight_color, highlight_rect, 2)
            self.screen.blit(text, rect)
