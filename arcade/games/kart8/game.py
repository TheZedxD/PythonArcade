import math
from pathlib import Path

import pygame

from state import State
from utils.persistence import load_json, save_json

from .engine.track import create_demo_track
from .engine.renderer import Renderer
from .engine.physics import Car, Ghost

BASE_PATH = Path(__file__).resolve().parents[2]
SAVE_PATH = BASE_PATH / "save" / "kart8.json"
DEFAULT_DATA = {
    "settings": {
        "difficulty": 1.0,
        "layout": "vertical",
        "fps": 60,
        "volume": 1.0,
        "show_help": True,
    },
    "times": {
        "1p": {"last": [], "best": []},
        "2p": {"last": [], "best": []},
    },
}

NUM_LAPS = 2


class KartGame(State):
    def startup(self, screen, num_players: int = 1, items: bool = True, **opts):
        super().startup(screen, num_players, **opts)
        self.track = create_demo_track()
        if not items:
            self.track.items = []
        self.items_enabled = items
        self.data = load_json(str(SAVE_PATH), DEFAULT_DATA)
        settings = self.data.get("settings", {})
        self.difficulty = settings.get("difficulty", 1.0)
        self.layout = settings.get("layout", "vertical")
        self.fps_cap = settings.get("fps", 60)
        self.volume = settings.get("volume", 1.0)
        self.show_help = settings.get("show_help", True)
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume)

        self.players = [Car(self.track)]
        if num_players > 1:
            self.players.append(Car(self.track, color=(255, 255, 0)))
            self.ghost = None
        else:
            self.ghost = Ghost(self.track, self.difficulty)
        self.laps = [0 for _ in self.players]
        self.lap_times = [[] for _ in self.players]
        self.timers = [0.0 for _ in self.players]
        self.font = pygame.font.SysFont("Courier", 20)
        self.hud_color = (0, 255, 0)
        self.create_help_surface()
        self.create_cameras()
        self.build_minimap()

    # ---- setup helpers -------------------------------------------------
    def create_cameras(self):
        w, h = self.screen.get_size()
        self.renderers = []
        self.cameras = []
        if self.num_players == 1:
            surf = pygame.Surface((w, h))
            if pygame.display.get_surface():
                surf = surf.convert()
            self.cameras.append(surf)
            self.renderers.append(Renderer(self.track))
        else:
            if self.layout == "vertical":
                size = (w, h // 2)
            else:
                size = (w // 2, h)
            for _ in range(2):
                surf = pygame.Surface(size)
                if pygame.display.get_surface():
                    surf = surf.convert()
                self.cameras.append(surf)
                self.renderers.append(Renderer(self.track))

    def build_minimap(self):
        w, h = 80, 60
        pts = []
        x = y = 0.0
        ang = 0.0
        step = self.track.total_length / 200
        z = 0.0
        while z < self.track.total_length:
            curve = self.track.curvature_at(z)
            ang += curve * step * 40
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            pts.append((x, y))
            z += step
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        scale = min((w - 10) / (maxx - minx + 1e-6), (h - 10) / (maxy - miny + 1e-6))
        self.map_points = [
            (int((px - minx) * scale) + 5, int((py - miny) * scale) + 5)
            for px, py in pts
        ]
        surf = pygame.Surface((w, h))
        if pygame.display.get_surface():
            surf = surf.convert()
        surf.fill((0, 0, 0))
        pygame.draw.lines(surf, (100, 100, 100), False, self.map_points, 1)
        self.minimap_template = surf
        self.map_step = step

    def create_help_surface(self):
        lines = [
            "Controls:",
            "P1 WASD + Shift boost",
            "P2 Arrows + RCtrl boost",
            "Tab toggle split",
            "Esc to menu",
        ]
        font = pygame.font.SysFont("Courier", 18)
        width = max(font.size(line)[0] for line in lines) + 20
        height = len(lines) * 24 + 10
        surf = pygame.Surface((width, height))
        surf.fill((0, 0, 0))
        surf.set_alpha(180)
        for i, line in enumerate(lines):
            text = font.render(line, True, (0, 255, 0))
            surf.blit(text, (10, 5 + i * 24))
        self.help_surface = surf

    # ---- input ---------------------------------------------------------
    def handle_keyboard(self, event):
        if event.type == pygame.KEYDOWN:
            if self.show_help:
                self.show_help = False
                self.data["settings"]["show_help"] = False
                save_json(str(SAVE_PATH), self.data)
            elif event.key == pygame.K_ESCAPE:
                self.done = True
                self.next = "menu"
            elif event.key == pygame.K_TAB and self.num_players > 1:
                self.layout = "horizontal" if self.layout == "vertical" else "vertical"
                self.data["settings"]["layout"] = self.layout
                save_json(str(SAVE_PATH), self.data)
                self.create_cameras()
            elif event.key == pygame.K_F3:
                self.fps_cap = 30 if self.fps_cap == 60 else 60
                self.data["settings"]["fps"] = self.fps_cap
                save_json(str(SAVE_PATH), self.data)
            elif event.key == pygame.K_F4:
                cycle = [0.8, 1.0, 1.2]
                idx = cycle.index(self.difficulty) if self.difficulty in cycle else 1
                self.difficulty = cycle[(idx + 1) % len(cycle)]
                if self.ghost:
                    self.ghost.difficulty = self.difficulty
                self.data["settings"]["difficulty"] = self.difficulty
                save_json(str(SAVE_PATH), self.data)
            elif event.key == pygame.K_MINUS:
                self.volume = max(0.0, round(self.volume - 0.1, 2))
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(self.volume)
                self.data["settings"]["volume"] = self.volume
                save_json(str(SAVE_PATH), self.data)
            elif event.key == pygame.K_EQUALS:
                self.volume = min(1.0, round(self.volume + 0.1, 2))
                if pygame.mixer.get_init():
                    pygame.mixer.music.set_volume(self.volume)
                self.data["settings"]["volume"] = self.volume
                save_json(str(SAVE_PATH), self.data)

    # ---- game logic ----------------------------------------------------
    def update(self, dt):
        keys = pygame.key.get_pressed()
        # player 1 controls
        controls1 = {
            "accelerate": keys[pygame.K_w],
            "brake": keys[pygame.K_s],
            "left": keys[pygame.K_a],
            "right": keys[pygame.K_d],
        }
        boost1 = keys[pygame.K_LSHIFT]
        prev_z1 = self.players[0].z
        self.players[0].update(dt, controls1, boost1)
        self.timers[0] += dt
        if prev_z1 > self.players[0].z:
            self.laps[0] += 1
            self.lap_times[0].append(self.timers[0])
            self.timers[0] = 0.0
            if len(self.lap_times[0]) >= NUM_LAPS:
                self.record_time(0)

        if self.num_players > 1:
            controls2 = {
                "accelerate": keys[pygame.K_UP],
                "brake": keys[pygame.K_DOWN],
                "left": keys[pygame.K_LEFT],
                "right": keys[pygame.K_RIGHT],
            }
            boost2 = keys[pygame.K_RCTRL]
            prev_z2 = self.players[1].z
            self.players[1].update(dt, controls2, boost2)
            self.timers[1] += dt
            if prev_z2 > self.players[1].z:
                self.laps[1] += 1
                self.lap_times[1].append(self.timers[1])
                self.timers[1] = 0.0
                if len(self.lap_times[1]) >= NUM_LAPS:
                    self.record_time(1)
        elif self.ghost:
            self.ghost.update(dt, self.players[0].z)

        # move shells and handle collisions
        if self.items_enabled:
            for item in self.track.items:
                if item.get("type") == "shell" and item.get("active", True):
                    item["z"] = (
                        item["z"] + item.get("speed", 0) * dt
                    ) % self.track.total_length
            for p in self.players:
                for item in self.track.items:
                    if not item.get("active", True):
                        continue
                    dz = self.track.relative_distance(p.z, item["z"])
                    if dz < 5 and abs(p.x - item["x"]) < 0.6:
                        t = item["type"]
                        if t == "boost":
                            p.speed = min(p.speed + 80, p.max_speed * 1.2)
                        elif t == "oil":
                            p.oil_timer = 2.0
                        elif t == "shell":
                            p.speed *= 0.5
                            item["active"] = False
        self.track.items = [i for i in self.track.items if i.get("active", True)]

    # ---- drawing -------------------------------------------------------
    def draw_hud(self, surface, player, lap):
        lap_text = self.font.render(f"LAP {lap + 1}", True, self.hud_color)
        surface.blit(lap_text, (10, 10))
        speed_text = self.font.render(f"{int(player.speed)}", True, self.hud_color)
        surface.blit(speed_text, (10, 40))
        if self.minimap_template:
            m = self.minimap_template.copy()
            idx = int(player.z / self.map_step) % len(self.map_points)
            pygame.draw.circle(m, player.color, self.map_points[idx], 2)
            surface.blit(m, (surface.get_width() - m.get_width() - 5, 5))

    def record_time(self, player_index: int):
        mode = "1p" if self.num_players == 1 else "2p"
        times = self.data.setdefault("times", {}).setdefault(
            mode, {"last": [], "best": []}
        )
        times["last"] = self.lap_times[player_index][:]
        total = sum(self.lap_times[player_index])
        best = times.get("best", []) + [total]
        times["best"] = sorted(best)[:5]
        save_json(str(SAVE_PATH), self.data)

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.num_players == 1:
            self.renderers[0].render(
                self.cameras[0],
                self.players[0],
                [self.ghost] if self.ghost else None,
                self.track.items if self.items_enabled else None,
            )
            self.draw_hud(self.cameras[0], self.players[0], self.laps[0])
            self.screen.blit(self.cameras[0], (0, 0))
        else:
            for i in range(2):
                others = [self.players[1 - i]]
                self.renderers[i].render(
                    self.cameras[i],
                    self.players[i],
                    others,
                    self.track.items if self.items_enabled else None,
                )
                self.draw_hud(self.cameras[i], self.players[i], self.laps[i])
            if self.layout == "vertical":
                h = self.screen.get_height() // 2
                self.screen.blit(self.cameras[0], (0, 0))
                self.screen.blit(self.cameras[1], (0, h))
            else:
                w = self.screen.get_width() // 2
                self.screen.blit(self.cameras[0], (0, 0))
                self.screen.blit(self.cameras[1], (w, 0))

        if self.show_help and self.help_surface:
            rect = self.help_surface.get_rect(center=self.screen.get_rect().center)
            self.screen.blit(self.help_surface, rect)


# expose Game class for loader
Game = KartGame
