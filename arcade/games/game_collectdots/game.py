import os
import random
import pygame
from state import State

class CollectDotsState(State):
    def startup(self, screen):
        super().startup(screen)
        self.font = pygame.font.SysFont("Courier", 24)
        self.big_font = pygame.font.SysFont("Courier", 32)
        self.score = 0
        self.player = pygame.Rect(screen.get_width() // 2 - 16,
                                   screen.get_height() // 2 - 16, 32, 32)
        self.dot = pygame.Rect(0, 0, 16, 16)
        self.respawn_dot()
        self.speed = 200
        self.state = "instructions"
        self.pause_options = ["Resume", "Quit to Menu"]
        self.pause_index = 0
        self.hs_path = os.path.join(os.path.dirname(__file__), "highscore.txt")
        if not os.path.isfile(self.hs_path):
            with open(self.hs_path, "w") as f:
                f.write("0")
        with open(self.hs_path) as f:
            self.high_score = int(f.read().strip() or 0)

    def respawn_dot(self):
        width, height = self.screen.get_size()
        x = random.randint(0, width - self.dot.width)
        y = random.randint(0, height - self.dot.height)
        self.dot.topleft = (x, y)

    def get_event(self, event):
        if self.state == "instructions":
            if event.type == pygame.KEYDOWN:
                self.state = "play"
        elif self.state == "play":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
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
                    elif choice == "Quit to Menu":
                        self.update_highscore()
                        self.done = True
                        self.next = "menu"

    def update_highscore(self):
        if self.score > self.high_score:
            self.high_score = self.score
            with open(self.hs_path, "w") as f:
                f.write(str(self.high_score))

    def update(self, dt):
        if self.state != "play":
            return
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        self.player.x += dx * self.speed * dt
        self.player.y += dy * self.speed * dt
        self.player.clamp_ip(self.screen.get_rect())
        if self.player.colliderect(self.dot):
            self.score += 1
            self.respawn_dot()

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.state == "instructions":
            text1 = self.big_font.render("Use arrow keys to move the square", True, (0, 255, 0))
            text2 = self.big_font.render("Press any key to start", True, (0, 255, 0))
            rect1 = text1.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 - 20))
            rect2 = text2.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2 + 20))
            self.screen.blit(text1, rect1)
            self.screen.blit(text2, rect2)
            return

        pygame.draw.rect(self.screen, (0, 255, 0), self.player)
        pygame.draw.ellipse(self.screen, (255, 0, 0), self.dot)
        score_text = self.font.render(f"Score: {self.score}", True, (0, 255, 0))
        self.screen.blit(score_text, (10, 10))

        if self.state == "pause":
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            self.screen.blit(overlay, (0, 0))
            for i, option in enumerate(self.pause_options):
                color = (0, 255, 0) if i == self.pause_index else (0, 155, 0)
                prefix = "> " if i == self.pause_index else "  "
                text = self.big_font.render(prefix + option, True, color)
                rect = text.get_rect(center=(self.screen.get_width() // 2,
                                             self.screen.get_height() // 2 + i * 40))
                self.screen.blit(text, rect)
