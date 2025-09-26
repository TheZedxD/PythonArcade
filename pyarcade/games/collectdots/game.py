import random
from datetime import datetime

import pygame

from ...common.theme import BG_COLOR, PRIMARY_COLOR, draw_text, get_font
from ...common.ui import PauseMenu
from ...state import State
from ...utils.persistence import load_json, save_json
from ...utils.resources import save_path

SETTINGS_PATH = save_path("settings.json")
HS_PATH = save_path("collectdots_highscores.json")


class CollectDotsState(State):
    def startup(self, screen, num_players: int = 1):
        super().startup(screen, num_players)
        self.font = get_font(24)
        self.score = 0
        self.score2 = 0
        cx, cy = screen.get_width() // 2, screen.get_height() // 2
        if self.num_players == 2:
            self.player = pygame.Rect(cx - 32, cy - 16, 32, 32)
            self.player2 = pygame.Rect(cx, cy - 16, 32, 32)
        else:
            self.player = pygame.Rect(cx - 16, cy - 16, 32, 32)
            self.player2 = None
        self.dot = pygame.Rect(0, 0, 16, 16)
        self.respawn_dot()
        self.speed = 200
        self.state = "instructions"
        self.pause_menu = PauseMenu(
            ["Resume", "Volume -", "Volume +", "Fullscreen", "Quit"],
            font_size=32,
        )
        self.hs_path = HS_PATH
        self.data = load_json(
            self.hs_path, {"highscore": 0, "plays": 0, "last_played": None}
        )
        self.high_score = self.data.get("highscore", 0)
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
        self.pad_dirs = {}
        self.overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

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
                self.pause_menu.index = 0
        elif self.state == "pause":
            choice = self.pause_menu.handle_keyboard(event)
            if choice:
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

    def handle_gamepad(self, event):
        if self.state == "instructions":
            if event.type in (
                pygame.JOYBUTTONDOWN,
                pygame.JOYAXISMOTION,
                pygame.JOYHATMOTION,
            ):
                self.state = "play"
        elif self.state == "play":
            if event.type == pygame.JOYBUTTONDOWN and event.button == 7:
                self.state = "pause"
                self.pause_menu.index = 0
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
            choice = self.pause_menu.handle_gamepad(event)
            if choice:
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

    def update_stats(self):
        best = self.score
        if self.num_players == 2:
            best = max(self.score, self.score2)
        if best > self.high_score:
            self.high_score = best
        self.data["highscore"] = self.high_score
        self.data["plays"] = self.data.get("plays", 0) + 1
        self.data["last_played"] = datetime.now().isoformat()
        save_json(self.hs_path, self.data)

    def update(self, dt):
        if self.state != "play":
            if self.state == "pause":
                pygame.mixer.music.set_volume(self.settings.get("sound_volume", 1.0))
            return
        keys = pygame.key.get_pressed()
        if self.num_players == 2:
            dx1 = dy1 = dx2 = dy2 = 0
            if keys[pygame.K_LEFT]:
                dx1 -= 1
            if keys[pygame.K_RIGHT]:
                dx1 += 1
            if keys[pygame.K_UP]:
                dy1 -= 1
            if keys[pygame.K_DOWN]:
                dy1 += 1
            if keys[pygame.K_a]:
                dx2 -= 1
            if keys[pygame.K_d]:
                dx2 += 1
            if keys[pygame.K_w]:
                dy2 -= 1
            if keys[pygame.K_s]:
                dy2 += 1
            self.player.x += dx1 * self.speed * dt
            self.player.y += dy1 * self.speed * dt
            self.player.clamp_ip(self.screen.get_rect())
            self.player2.x += dx2 * self.speed * dt
            self.player2.y += dy2 * self.speed * dt
            self.player2.clamp_ip(self.screen.get_rect())
            if self.player.colliderect(self.dot):
                self.score += 1
                self.respawn_dot()
            elif self.player2.colliderect(self.dot):
                self.score2 += 1
                self.respawn_dot()
        else:
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
        self.screen.fill(BG_COLOR)
        if self.state == "instructions":
            if self.num_players == 2:
                draw_text(
                    self.screen,
                    "P1: Arrows  P2: WASD",
                    (
                        self.screen.get_width() // 2,
                        self.screen.get_height() // 2 - 20,
                    ),
                    32,
                    PRIMARY_COLOR,
                    center=True,
                )
            else:
                draw_text(
                    self.screen,
                    "Use arrow keys to move the square",
                    (
                        self.screen.get_width() // 2,
                        self.screen.get_height() // 2 - 20,
                    ),
                    32,
                    PRIMARY_COLOR,
                    center=True,
                )
            draw_text(
                self.screen,
                "Press any key to start",
                (
                    self.screen.get_width() // 2,
                    self.screen.get_height() // 2 + 20,
                ),
                32,
                PRIMARY_COLOR,
                center=True,
            )
            return

        pygame.draw.rect(self.screen, PRIMARY_COLOR, self.player)
        if self.num_players == 2 and self.player2:
            pygame.draw.rect(self.screen, (0, 0, 255), self.player2)
        pygame.draw.ellipse(self.screen, (255, 0, 0), self.dot)
        if self.num_players == 2:
            score1 = self.font.render(f"P1: {self.score}", True, PRIMARY_COLOR)
            score2 = self.font.render(f"P2: {self.score2}", True, PRIMARY_COLOR)
            self.screen.blit(score1, (10, 10))
            rect2 = score2.get_rect(topright=(self.screen.get_width() - 10, 10))
            self.screen.blit(score2, rect2)
        else:
            score_text = self.font.render(f"Score: {self.score}", True, PRIMARY_COLOR)
            self.screen.blit(score_text, (10, 10))

        if self.state == "pause":
            self.overlay.fill((0, 0, 0, 200))
            self.pause_menu.draw(self.overlay)
            self.screen.blit(self.overlay, (0, 0))
