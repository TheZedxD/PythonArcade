import os
import random
from datetime import datetime
import pygame
from state import State
from utils.persistence import load_json, save_json

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
        self.hs_path = os.path.join(os.path.dirname(__file__), "highscores.json")
        self.data = load_json(self.hs_path,
                              {"highscore": 0, "plays": 0, "last_played": None})
        self.high_score = self.data.get("highscore", 0)
        self.pad_dirs = {}

    def respawn_dot(self):
        width, height = self.screen.get_size()
        x = random.randint(0, width - self.dot.width)
        y = random.randint(0, height - self.dot.height)
        self.dot.topleft = (x, y)

    def handle_keyboard(self, event):
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
                        self.update_stats()
                        self.done = True
                        self.next = "menu"

    def handle_gamepad(self, event):
        if self.state == "instructions":
            if event.type in (pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION,
                               pygame.JOYHATMOTION):
                self.state = "play"
        elif self.state == "play":
            if event.type == pygame.JOYBUTTONDOWN and event.button == 7:
                self.state = "pause"
                self.pause_index = 0
            elif event.type == pygame.JOYAXISMOTION:
                if event.axis in (0, 1):
                    dirs = self.pad_dirs.setdefault(event.joy, [0, 0])
                    if event.axis == 0:
                        dirs[0] = event.value if abs(event.value) > 0.2 else 0
                    else:
                        dirs[1] = event.value if abs(event.value) > 0.2 else 0
            elif event.type == pygame.JOYHATMOTION:
                dirs = self.pad_dirs.setdefault(event.joy, [0, 0])
                dirs[0] = event.value[0]
                dirs[1] = -event.value[1]
        elif self.state == "pause":
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
                    elif choice == "Quit to Menu":
                        self.update_stats()
                        self.done = True
                        self.next = "menu"
                elif event.button in (1, 7, 9):
                    self.state = "play"

    def update_stats(self):
        if self.score > self.high_score:
            self.high_score = self.score
        self.data["highscore"] = self.high_score
        self.data["plays"] = self.data.get("plays", 0) + 1
        self.data["last_played"] = datetime.now().isoformat()
        save_json(self.hs_path, self.data)

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
        pad_dx = pad_dy = 0
        for px, py in self.pad_dirs.values():
            pad_dx += px
            pad_dy += py
        self.player.x += (dx + pad_dx) * self.speed * dt
        self.player.y += (dy + pad_dy) * self.speed * dt
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
