import math
import pygame
from state import State
from .engine.track import create_demo_track
from .engine.renderer import Renderer
from .engine.physics import Car, Ghost


class KartGame(State):
    def startup(self, screen, num_players: int = 1, items: bool = True, **opts):
        super().startup(screen, num_players, **opts)
        self.track = create_demo_track()
        if not items:
            self.track.items = []
        self.items_enabled = items
        self.players = [Car(self.track)]
        if num_players > 1:
            self.players.append(Car(self.track, color=(255, 255, 0)))
            self.ghost = None
        else:
            self.ghost = Ghost(self.track)
        self.laps = [0 for _ in self.players]
        self.font = pygame.font.SysFont("Courier", 20)
        self.hud_color = (0, 255, 0)
        self.layout = "vertical"  # top/bottom by default
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
            (int((px - minx) * scale) + 5, int((py - miny) * scale) + 5) for px, py in pts
        ]
        surf = pygame.Surface((w, h))
        if pygame.display.get_surface():
            surf = surf.convert()
        surf.fill((0, 0, 0))
        pygame.draw.lines(surf, (100, 100, 100), False, self.map_points, 1)
        self.minimap_template = surf
        self.map_step = step

    # ---- input ---------------------------------------------------------
    def handle_keyboard(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.done = True
                self.next = "menu"
            elif event.key == pygame.K_TAB and self.num_players > 1:
                self.layout = "horizontal" if self.layout == "vertical" else "vertical"
                self.create_cameras()

    # ---- game logic ----------------------------------------------------
    def update(self, dt):
        keys = pygame.key.get_pressed()
        # player 1 controls
        controls1 = {
            'accelerate': keys[pygame.K_w],
            'brake': keys[pygame.K_s],
            'left': keys[pygame.K_a],
            'right': keys[pygame.K_d],
        }
        boost1 = keys[pygame.K_LSHIFT]
        prev_z1 = self.players[0].z
        self.players[0].update(dt, controls1, boost1)
        if prev_z1 > self.players[0].z:
            self.laps[0] += 1

        if self.num_players > 1:
            controls2 = {
                'accelerate': keys[pygame.K_UP],
                'brake': keys[pygame.K_DOWN],
                'left': keys[pygame.K_LEFT],
                'right': keys[pygame.K_RIGHT],
            }
            boost2 = keys[pygame.K_RCTRL]
            prev_z2 = self.players[1].z
            self.players[1].update(dt, controls2, boost2)
            if prev_z2 > self.players[1].z:
                self.laps[1] += 1
        elif self.ghost:
            self.ghost.update(dt, self.players[0].z)

        # move shells and handle collisions
        if self.items_enabled:
            for item in self.track.items:
                if item.get("type") == "shell" and item.get("active", True):
                    item["z"] = (item["z"] + item.get("speed", 0) * dt) % self.track.total_length
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

    def draw(self):
        self.screen.fill((0, 0, 0))
        if self.num_players == 1:
            self.renderers[0].render(self.cameras[0], self.players[0],
                                    [self.ghost] if self.ghost else None,
                                    self.track.items if self.items_enabled else None)
            self.draw_hud(self.cameras[0], self.players[0], self.laps[0])
            self.screen.blit(self.cameras[0], (0, 0))
        else:
            for i in range(2):
                others = [self.players[1 - i]]
                self.renderers[i].render(self.cameras[i], self.players[i], others,
                                        self.track.items if self.items_enabled else None)
                self.draw_hud(self.cameras[i], self.players[i], self.laps[i])
            if self.layout == "vertical":
                h = self.screen.get_height() // 2
                self.screen.blit(self.cameras[0], (0, 0))
                self.screen.blit(self.cameras[1], (0, h))
            else:
                w = self.screen.get_width() // 2
                self.screen.blit(self.cameras[0], (0, 0))
                self.screen.blit(self.cameras[1], (w, 0))


# expose Game class for loader
Game = KartGame

