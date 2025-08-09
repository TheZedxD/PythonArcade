import pygame


class Renderer:
    def __init__(self, screen, track):
        self.screen = screen
        self.track = track
        self.scale = 200.0  # scaling factor for width
        self.cam_height = 1.0

    def project(self, obj_z, obj_x, player):
        dz = obj_z - player.z
        if dz < 0:
            dz += self.track.total_length
        if dz <= 1e-2:
            return None
        # depth to screen row
        y = int(self.cam_height / dz)
        horizon = self.screen.get_height() // 2
        screen_y = horizon + y
        if screen_y >= self.screen.get_height():
            return None
        curve = self.track.curvature_at(player.z)
        center = self.screen.get_width() / 2 - curve * dz * dz
        scale = self.scale / dz
        screen_x = center + obj_x * scale
        return screen_x, screen_y, scale

    def render_road(self, player):
        width, height = self.screen.get_size()
        horizon = height // 2
        self.screen.fill((50, 50, 50), (0, 0, width, horizon))
        x = 0.0
        dx = 0.0
        for y in range(height - 1, horizon, -1):
            perspective = self.cam_height / (y - horizon)
            world_z = player.z + perspective
            seg, _, _ = self.track.segment_at(world_z)
            if not seg:
                continue
            dx += seg.curvature * perspective
            x += dx
            road_w = self.scale / perspective
            center = width / 2 - x + player.x * road_w * 0.02
            left = int(center - road_w)
            right = int(center + road_w)
            if right < 0 or left > width:
                continue
            color_index = int(world_z) // 3
            road_color = (100, 100, 100) if color_index % 2 else (110, 110, 110)
            shoulder_color = (200, 200, 200) if color_index % 2 else (220, 220, 220)
            grass_color = (16, 120, 16) if color_index % 2 else (0, 170, 0)
            pygame.draw.rect(self.screen, grass_color, pygame.Rect(0, y, left, 1))
            pygame.draw.rect(self.screen, grass_color, pygame.Rect(right, y, width - right, 1))
            pygame.draw.rect(self.screen, shoulder_color, pygame.Rect(left, y, 2, 1))
            pygame.draw.rect(self.screen, shoulder_color, pygame.Rect(right - 2, y, 2, 1))
            pygame.draw.rect(self.screen, road_color, pygame.Rect(left + 2, y, right - left - 4, 1))

    def render_billboards(self, player):
        for z, x, color in sorted(self.track.billboards,
                                  key=lambda b: -self.track.relative_distance(player.z, b[0])):
            res = self.project(z, x, player)
            if not res:
                continue
            sx, sy, scale = res
            size = max(5, int(20 * scale / self.scale))
            rect = pygame.Rect(int(sx) - size // 2, int(sy) - size, size, size)
            pygame.draw.rect(self.screen, color, rect)

    def render_car(self, car, player):
        res = self.project(car.z, car.x, player)
        if not res:
            return
        sx, sy, scale = res
        w = int(20 * scale / self.scale)
        h = int(40 * scale / self.scale)
        rect = pygame.Rect(int(sx) - w // 2, int(sy) - h, w, h)
        pygame.draw.rect(self.screen, car.color, rect)

    def render_player_car(self):
        width, height = self.screen.get_size()
        rect = pygame.Rect(width // 2 - 10, height - 40, 20, 40)
        pygame.draw.rect(self.screen, (0, 0, 255), rect)

    def render(self, player, others=None):
        self.render_road(player)
        self.render_billboards(player)
        if others:
            for obj in sorted(others, key=lambda o: -self.track.relative_distance(player.z, o.z)):
                self.render_car(obj, player)
        self.render_player_car()
