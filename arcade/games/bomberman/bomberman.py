"""Matrix-themed Bomberman clone scaffolding."""

from __future__ import annotations

import os
import random
import pygame

from state import State
from utils.persistence import load_json
from common.theme import PRIMARY_COLOR, draw_text
from common.ui import PauseMenu

from .level import Level, TILE_SIZE
from .player import Player, Controls
from .enemy import Enemy
from .bomb import Bomb
from .explosion import Explosion
from .powerups import PowerUp

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
SETTINGS_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "settings.json")
DEFAULT_CONFIG = {
    "map_size": [15, 13],
    "enemy_count": 3,
    "fuse_ms": 2000,
    "base_blast_radius": 2,
    "max_bombs_per_player": 1,
    "max_blast_radius": 5,
    "powerup_chance": 0.2,
}


class BombermanGame(State):
    fps_cap = 60

    def startup(self, screen, num_players: int = 1, **opts):
        super().startup(screen, num_players, **opts)
        self.config = load_json(CONFIG_PATH, DEFAULT_CONFIG)
        self.settings = load_json(
            SETTINGS_PATH,
            {
                "window_size": [800, 600],
                "fullscreen": False,
                "sound_volume": 1.0,
                "keybindings": {},
            },
        )
        self.assets = self._load_assets()
        width, height = self.config.get("map_size", [15, 13])
        self.level = Level.generate_random(width, height)
        self.players: list[Player] = []
        p1_controls = Controls(
            up=pygame.K_UP,
            down=pygame.K_DOWN,
            left=pygame.K_LEFT,
            right=pygame.K_RIGHT,
            bomb=pygame.K_SPACE,
        )
        self.players.append(Player(1, 1, p1_controls, self.assets["player1"]))
        self.players[0].radius = self.config.get("base_blast_radius", 2)
        self.players[0].max_bombs = self.config.get("max_bombs_per_player", 1)
        if self.num_players == 2:
            p2_controls = Controls(
                up=pygame.K_w,
                down=pygame.K_s,
                left=pygame.K_a,
                right=pygame.K_d,
                bomb=pygame.K_LSHIFT,
            )
            p2 = Player(
                self.level.width - 2,
                self.level.height - 2,
                p2_controls,
                self.assets["player2"],
            )
            p2.radius = self.config.get("base_blast_radius", 2)
            p2.max_bombs = self.config.get("max_bombs_per_player", 1)
            self.players.append(p2)
        self.enemy_speed = self.config.get("enemy_speed", 0.5)
        self.enemies = self._spawn_enemies()
        self.bombs: list[Bomb] = []
        self.explosions: list[Explosion] = []
        self.powerups: list[PowerUp] = []
        self.pause_menu = PauseMenu(["Resume", "Return to Menu"], font_size=32)
        self.state = "play"
        self.game_timer = 0.0
        self.time_limit = self.config.get("time_limit", 0)
        self.time_left = float(self.time_limit)
        self.end_timer = 0.0
        self.overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

    # ------------------------------------------------------------------ utils
    def _load_assets(self) -> dict[str, pygame.surface.Surface]:
        """Generate simple colored surfaces instead of loading images."""

        def surface(color: tuple[int, int, int]) -> pygame.surface.Surface:
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill(color)
            return surf

        assets = {
            "wall": surface((0, 40, 0)),
            "brick": surface((0, 80, 0)),
            "player1": surface((0, 200, 0)),
            "player2": surface((0, 200, 80)),
            "enemy": surface((200, 0, 0)),
            "bomb": surface((0, 0, 0)),
            "blast": surface((200, 200, 0)),
            "powerup": surface((0, 200, 200)),
        }

        # add simple details
        pygame.draw.circle(
            assets["bomb"],
            (150, 150, 150),
            (TILE_SIZE // 2, TILE_SIZE // 2),
            TILE_SIZE // 2,
        )
        pygame.draw.rect(assets["player1"], (0, 0, 0), assets["player1"].get_rect(), 2)
        pygame.draw.rect(assets["player2"], (0, 0, 0), assets["player2"].get_rect(), 2)
        pygame.draw.rect(assets["enemy"], (0, 0, 0), assets["enemy"].get_rect(), 2)

        return assets

    def _spawn_enemies(self) -> list[Enemy]:
        enemies: list[Enemy] = []
        for _ in range(self.config.get("enemy_count", 0)):
            while True:
                x = random.randint(1, self.level.width - 2)
                y = random.randint(1, self.level.height - 2)
                if self.level.is_blocked(x, y):
                    continue
                if (x, y) in [(p.x, p.y) for p in self.players]:
                    continue
                enemies.append(Enemy(x, y, self.assets["enemy"], self.enemy_speed))
                break
        return enemies

    def _spawn_powerups(self, tiles: list[tuple[int, int]]) -> None:
        """Randomly create power-ups on destroyed brick tiles."""

        chance = self.config.get("powerup_chance", 0.0)
        for x, y in tiles:
            if random.random() < chance:
                self.powerups.append(PowerUp(x, y, "radius", self.assets["powerup"]))

    def _check_deaths(self) -> None:
        """Remove players caught in explosions."""

        tiles = {(e.x, e.y) for e in self.explosions}
        for player in list(self.players):
            if (player.x, player.y) in tiles:
                self.players.remove(player)

    def _collect_powerups(self) -> None:
        """Check for player collisions with power-ups."""

        max_radius = self.config.get("max_blast_radius", 5)
        for powerup in list(self.powerups):
            for player in self.players:
                if player.x == powerup.x and player.y == powerup.y:
                    if powerup.kind == "radius":
                        player.radius = min(player.radius + 1, max_radius)
                    self.powerups.remove(powerup)
                    break

    def _next_level(self) -> None:
        """Regenerate level and respawn enemies for single-player progression."""

        width, height = self.config.get("map_size", [15, 13])
        self.level = Level.generate_random(width, height)
        self.bombs.clear()
        self.explosions.clear()
        self.powerups.clear()
        for i, player in enumerate(self.players):
            if i == 0:
                player.x, player.y = 1, 1
            else:
                player.x, player.y = self.level.width - 2, self.level.height - 2
        self.enemies = self._spawn_enemies()
        self.state = "play"
        self.game_timer = 0.0
        if self.time_limit > 0:
            self.time_left = float(self.time_limit)

    # ------------------------------------------------------------------ events
    def handle_keyboard(self, event: pygame.event.Event) -> None:
        if self.state == "play":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = "pause"
                    self.pause_menu.index = 0
                for player in self.players:
                    if event.key == player.controls.bomb:
                        player.drop_bomb(self.bombs, self.config.get("fuse_ms", 2000))
        elif self.state == "pause":
            choice = self.pause_menu.handle_keyboard(event)
            if choice == "Resume":
                self.state = "play"
            elif choice == "Return to Menu":
                self.done = True
                self.next = "menu"

    def handle_gamepad(
        self, event: pygame.event.Event
    ) -> None:  # pragma: no cover - placeholder
        pass

    def handle_mouse(
        self, event: pygame.event.Event
    ) -> None:  # pragma: no cover - unused
        pass

    # ------------------------------------------------------------------ update
    def update(self, dt: float) -> None:
        if self.state == "pause":
            return
        if self.state in ("cleared", "defeat"):
            self.end_timer -= dt
            if self.end_timer <= 0:
                if self.state == "cleared":
                    self._next_level()
                else:
                    self.done = True
                    self.next = "menu"
            return
        # play state
        if self.time_limit > 0:
            self.time_left -= dt
            if self.time_left <= 0:
                self.state = "defeat"
                self.end_timer = 2.0
                return
        else:
            self.game_timer += dt
        keys = pygame.key.get_pressed()
        for player in self.players:
            player.handle_input(keys, self.level, self.bombs)
        for enemy in list(self.enemies):
            if not enemy.update(dt, self.level, self.bombs, self.explosions):
                self.enemies.remove(enemy)
        for bomb in list(self.bombs):
            if bomb.update(dt):
                explosions, destroyed = bomb.explode(self.level)
                self.explosions.extend(explosions)
                self._spawn_powerups(destroyed)
                self.bombs.remove(bomb)
        for expl in list(self.explosions):
            if expl.update(dt):
                self.explosions.remove(expl)
        self._check_deaths()
        self._collect_powerups()
        if self.num_players == 1 and not self.players:
            self.state = "defeat"
            self.end_timer = 2.0
        if self.num_players == 2 and len(self.players) <= 1:
            self.state = "defeat"
            self.end_timer = 2.0
        if not self.enemies:
            self.state = "cleared"
            self.end_timer = 2.0

    # ------------------------------------------------------------------ draw
    def draw(self) -> None:
        self.level.draw(self.screen, self.assets)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for bomb in self.bombs:
            bomb.draw(self.screen, self.assets["bomb"])
        for expl in self.explosions:
            expl.draw(self.screen, self.assets["blast"])
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for player in self.players:
            player.draw(self.screen)
        # HUD
        mode_text = f"{'1P' if self.num_players == 1 else '2P'} Mode"
        draw_text(self.screen, mode_text, (10, 10), 24, PRIMARY_COLOR)
        draw_text(
            self.screen,
            f"Enemies: {len(self.enemies)}",
            (10, 40),
            24,
            PRIMARY_COLOR,
        )
        if self.num_players == 1:
            if self.time_limit > 0:
                draw_text(
                    self.screen,
                    f"Time: {int(self.time_left)}",
                    (10, 70),
                    24,
                    PRIMARY_COLOR,
                )
            else:
                draw_text(
                    self.screen,
                    f"Time: {self.game_timer:0.1f}",
                    (10, 70),
                    24,
                    PRIMARY_COLOR,
                )
        if self.state == "pause":
            self.overlay.fill((0, 0, 0, 200))
            self.pause_menu.draw(self.overlay)
            self.screen.blit(self.overlay, (0, 0))
        elif self.state in ("cleared", "defeat"):
            self.overlay.fill((0, 0, 0, 200))
            text = "CLEARED" if self.state == "cleared" else "DEFEAT"
            draw_text(
                self.overlay,
                text,
                (self.screen.get_width() // 2, self.screen.get_height() // 2),
                48,
                PRIMARY_COLOR,
                center=True,
            )
            self.screen.blit(self.overlay, (0, 0))


def run() -> None:
    """Run the game directly."""
    pygame.init()
    config = load_json(CONFIG_PATH, DEFAULT_CONFIG)
    width, height = config.get("map_size", [15, 13])
    screen = pygame.display.set_mode((width * TILE_SIZE, height * TILE_SIZE))
    game = BombermanGame()
    game.startup(screen)
    clock = pygame.time.Clock()
    running = True
    while running and not game.done and not game.quit:
        dt = clock.tick(game.fps_cap) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                game.get_event(event)
        game.update(dt)
        game.draw()
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":  # pragma: no cover - manual run
    run()
