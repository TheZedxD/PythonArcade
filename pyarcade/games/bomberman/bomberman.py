"""Matrix-themed Bomberman clone scaffolding."""

from __future__ import annotations

import random
from pathlib import Path

import pygame

from ...common.theme import ACCENT_COLOR, PRIMARY_COLOR, draw_text, terminal_panel
from ...common.ui import PauseMenu
from ...state import State
from ...utils.persistence import load_json
from ...utils.resources import save_path
from .bomb import Bomb
from .enemy import Enemy
from .explosion import Explosion
from .level import TILE_SIZE, Level
from .player import Controls, Player
from .powerups import PowerUp

BASE_PATH = Path(__file__).resolve().parent
CONFIG_PATH = BASE_PATH / "config.json"
SETTINGS_PATH = save_path("settings.json")
DEFAULT_CONFIG = {
    "map_size": [15, 13],
    "enemy_count": 3,
    "fuse_ms": 2000,
    "base_blast_radius": 2,
    "max_bombs_per_player": 1,
    "max_blast_radius": 5,
    "max_enemy_count": 9,
    "min_fuse_ms": 500,
    "max_fuse_ms": 5000,
    "max_bomb_limit": 9,
    "powerup_chance": 0.2,
    "time_limit": 0,
}


class BombermanGame(State):
    fps_cap = 60

    def startup(self, screen, num_players: int = 1, **opts):
        super().startup(screen, num_players, **opts)
        cfg = load_json(CONFIG_PATH, DEFAULT_CONFIG)
        max_enemy = cfg.get("max_enemy_count", 9)
        cfg["enemy_count"] = max(0, min(cfg.get("enemy_count", 3), max_enemy))
        cfg["max_enemy_count"] = max_enemy
        min_fuse = cfg.get("min_fuse_ms", 500)
        max_fuse = cfg.get("max_fuse_ms", 5000)
        cfg["fuse_ms"] = max(min_fuse, min(cfg.get("fuse_ms", 2000), max_fuse))
        cfg["min_fuse_ms"] = min_fuse
        cfg["max_fuse_ms"] = max_fuse
        max_bomb_limit = cfg.get("max_bomb_limit", 9)
        cfg["max_bombs_per_player"] = max(
            1, min(cfg.get("max_bombs_per_player", 1), max_bomb_limit)
        )
        cfg["max_bomb_limit"] = max_bomb_limit
        max_radius = cfg.get("max_blast_radius", 5)
        cfg["base_blast_radius"] = max(
            1, min(cfg.get("base_blast_radius", 2), max_radius)
        )
        cfg["max_blast_radius"] = max_radius
        self.config = cfg
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
        self.pause_menu = PauseMenu(["Resume", "Return to Menu"], font_size=32)
        self.victory_menu = PauseMenu(["Restart", "Return to Menu"], font_size=32)
        self.overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        self.enemy_speed = self.config.get("enemy_speed", 0.5)
        # settings screen options
        self.settings_options = [
            "Mode",
            "Map Size",
            "Enemy Count",
            "Bomb Fuse",
            "Max Bombs",
            "Audio",
            "Start",
            "Back",
        ]
        self.settings_index = 0
        self.mode = 1
        self.map_sizes = [
            ("Small", (13, 11)),
            ("Medium", (15, 13)),
            ("Large", (17, 15)),
        ]
        self.map_size_index = 1
        self.enemy_count = self.config.get("enemy_count", 3)
        self.fuse_ms = self.config.get("fuse_ms", 2000)
        self.max_bombs = self.config.get("max_bombs_per_player", 1)
        self.audio_on = True
        self.prev_volume = self.settings.get("sound_volume", 1.0)
        self.state = "settings"
        self.winner = 0
        self.level: Level | None = None
        self.players: list[Player] = []
        self.p1: Player | None = None
        self.p2: Player | None = None
        self.enemies: list[Enemy] = []
        self.bombs: list[Bomb] = []
        self.explosions: list[Explosion] = []
        self.powerups: list[PowerUp] = []
        self.game_timer = 0.0
        self.time_limit = self.config.get("time_limit", 0)
        self.time_left = float(self.time_limit)
        self.end_timer = 0.0

    # ------------------------------------------------------------------ utils
    def _load_assets(self) -> dict[str, pygame.surface.Surface]:
        """Load image assets relative to this module with graceful fallbacks."""

        asset_dir = BASE_PATH / "assets"
        placeholders: dict[str, bool] = {}

        def load_image(
            name: str, color: tuple[int, int, int]
        ) -> pygame.surface.Surface:
            path = asset_dir / f"{name}.png"
            if path.is_file():
                try:
                    return pygame.image.load(str(path)).convert_alpha()
                except pygame.error:
                    pass
            surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            surf.fill(color)
            placeholders[name] = True
            return surf

        assets = {
            "wall": load_image("wall", (0, 40, 0)),
            "brick": load_image("brick", (0, 80, 0)),
            "player1": load_image("player1", (0, 200, 0)),
            "player2": load_image("player2", (0, 200, 80)),
            "enemy": load_image("enemy", (200, 0, 0)),
            "bomb": load_image("bomb", (0, 0, 0)),
            "blast": load_image("blast", (200, 200, 0)),
            "powerup": load_image("powerup", (0, 200, 200)),
        }

        # add simple details to placeholders to keep the Matrix look
        if placeholders.get("bomb"):
            pygame.draw.circle(
                assets["bomb"],
                (150, 150, 150),
                (TILE_SIZE // 2, TILE_SIZE // 2),
                TILE_SIZE // 2,
            )
        if placeholders.get("player1"):
            pygame.draw.rect(
                assets["player1"], (0, 0, 0), assets["player1"].get_rect(), 2
            )
        if placeholders.get("player2"):
            pygame.draw.rect(
                assets["player2"], (0, 0, 0), assets["player2"].get_rect(), 2
            )
        if placeholders.get("enemy"):
            pygame.draw.rect(assets["enemy"], (0, 0, 0), assets["enemy"].get_rect(), 2)

        return assets

    def _start_game(self, num_players: int) -> None:
        """Initialise a new round."""

        width, height = self.config.get("map_size", [15, 13])
        self.level = Level.generate_random(width, height)
        self.players = []
        self.bombs = []
        self.explosions = []
        self.powerups = []
        self.num_players = num_players
        p1_controls = Controls(
            up=pygame.K_UP,
            down=pygame.K_DOWN,
            left=pygame.K_LEFT,
            right=pygame.K_RIGHT,
            bomb=pygame.K_SPACE,
        )
        self.p1 = Player(1, 1, p1_controls, self.assets["player1"])
        self.p1.radius = self.config.get("base_blast_radius", 2)
        self.p1.max_bombs = self.config.get("max_bombs_per_player", 1)
        self.players.append(self.p1)
        if num_players == 2:
            p2_controls = Controls(
                up=pygame.K_w,
                down=pygame.K_s,
                left=pygame.K_a,
                right=pygame.K_d,
                bomb=pygame.K_LSHIFT,
            )
            self.p2 = Player(
                self.level.width - 2,
                self.level.height - 2,
                p2_controls,
                self.assets["player2"],
            )
            self.p2.radius = self.config.get("base_blast_radius", 2)
            self.p2.max_bombs = self.config.get("max_bombs_per_player", 1)
            self.players.append(self.p2)
            self.enemies = []
        else:
            self.p2 = None
            self.enemies = self._spawn_enemies()
        self.game_timer = 0.0
        self.time_limit = 0 if num_players == 2 else self.config.get("time_limit", 0)
        if self.time_limit > 0:
            self.time_left = float(self.time_limit)
        self.state = "play"

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

    def _option_value(self, option: str) -> str:
        if option == "Mode":
            return "1P" if self.mode == 1 else "2P"
        if option == "Map Size":
            return self.map_sizes[self.map_size_index][0]
        if option == "Enemy Count":
            return str(self.enemy_count) if self.mode == 1 else "N/A"
        if option == "Bomb Fuse":
            return f"{self.fuse_ms} ms"
        if option == "Max Bombs":
            return str(self.max_bombs)
        if option == "Audio":
            return "On" if self.audio_on else "Off"
        return ""

    def _adjust(self, delta: int) -> None:
        option = self.settings_options[self.settings_index]
        if option == "Mode":
            self.mode = 1 if self.mode == 2 else 2
        elif option == "Map Size":
            self.map_size_index = (self.map_size_index + delta) % len(self.map_sizes)
        elif option == "Enemy Count" and self.mode == 1:
            limit = self.config.get("max_enemy_count", 9)
            self.enemy_count = max(0, min(limit, self.enemy_count + delta))
        elif option == "Bomb Fuse":
            min_fuse = self.config.get("min_fuse_ms", 500)
            max_fuse = self.config.get("max_fuse_ms", 5000)
            self.fuse_ms = max(min_fuse, min(max_fuse, self.fuse_ms + delta * 500))
        elif option == "Max Bombs":
            limit = self.config.get("max_bomb_limit", 9)
            self.max_bombs = max(1, min(limit, self.max_bombs + delta))
        elif option == "Audio" and delta != 0:
            self.audio_on = not self.audio_on

    def _apply_settings(self) -> None:
        self.config["map_size"] = list(self.map_sizes[self.map_size_index][1])
        self.config["enemy_count"] = self.enemy_count if self.mode == 1 else 0
        self.config["fuse_ms"] = self.fuse_ms
        self.config["max_bombs_per_player"] = self.max_bombs
        pygame.mixer.music.set_volume(self.prev_volume if self.audio_on else 0)

    # ------------------------------------------------------------------ events
    def handle_keyboard(self, event: pygame.event.Event) -> None:
        if self.state == "settings":
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    self.settings_index = (self.settings_index + 1) % len(
                        self.settings_options
                    )
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.settings_index = (self.settings_index - 1) % len(
                        self.settings_options
                    )
                elif event.key in (pygame.K_LEFT, pygame.K_a):
                    self._adjust(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._adjust(1)
                elif event.key == pygame.K_RETURN:
                    option = self.settings_options[self.settings_index]
                    if option == "Start":
                        self._apply_settings()
                        self._start_game(self.mode)
                    elif option in ("Back", "Menu"):
                        self.done = True
                        self.next = "menu"
                elif event.key == pygame.K_ESCAPE:
                    self.done = True
                    self.next = "menu"
        elif self.state == "play":
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
        elif self.state == "victory":
            choice = self.victory_menu.handle_keyboard(event)
            if choice == "Restart":
                self._start_game(self.num_players)
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
        if self.state in ("pause", "settings", "victory"):
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
            if bomb not in self.bombs:
                # bomb may have been removed via chain reaction
                continue
            if bomb.update(dt):
                explosions, destroyed = bomb.explode(self.level, self.bombs)
                self.explosions.extend(explosions)
                self._spawn_powerups(destroyed)
                if bomb in self.bombs:
                    self.bombs.remove(bomb)
        for expl in list(self.explosions):
            if expl.update(dt):
                self.explosions.remove(expl)
        self._check_deaths()
        self._collect_powerups()
        if self.num_players == 1:
            if not self.players:
                self.state = "defeat"
                self.end_timer = 2.0
            elif not self.enemies:
                self.state = "cleared"
                self.end_timer = 2.0
        else:
            if len(self.players) == 1:
                self.winner = 1 if self.players[0] is self.p1 else 2
                self.state = "victory"
                self.victory_menu.index = 0
            elif len(self.players) == 0:
                self.winner = 0
                self.state = "victory"
                self.victory_menu.index = 0

    # ------------------------------------------------------------------ draw
    def draw(self) -> None:
        if self.state == "settings":
            self.screen.fill((0, 0, 0))
            rect = self.screen.get_rect().inflate(-200, -200)
            terminal_panel(self.screen, rect)
            draw_text(
                self.screen,
                "BOMBERMAN SETTINGS",
                (rect.centerx, rect.top + 40),
                32,
                PRIMARY_COLOR,
                center=True,
            )
            for i, option in enumerate(self.settings_options):
                color = PRIMARY_COLOR if i == self.settings_index else ACCENT_COLOR
                prefix = "> " if i == self.settings_index else "  "
                value = self._option_value(option)
                text = f"{prefix}{option}"
                if value:
                    text += f": {value}"
                draw_text(
                    self.screen,
                    text,
                    (rect.centerx, rect.top + 80 + i * 40),
                    24,
                    color,
                    center=True,
                )
            return

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
        if self.num_players == 1:
            draw_text(
                self.screen,
                f"Enemies: {len(self.enemies)}",
                (10, 40),
                24,
                PRIMARY_COLOR,
            )
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
        elif self.state == "victory":
            self.overlay.fill((0, 0, 0, 200))
            text = "DRAW" if self.winner == 0 else f"PLAYER {self.winner} WINS"
            draw_text(
                self.overlay,
                text,
                (
                    self.screen.get_width() // 2,
                    self.screen.get_height() // 2 - 60,
                ),
                48,
                PRIMARY_COLOR,
                center=True,
            )
            self.victory_menu.draw(self.overlay)
            self.screen.blit(self.overlay, (0, 0))

    def cleanup(self) -> None:
        pygame.mixer.music.set_volume(self.prev_volume)
        self.level = None
        self.players.clear()
        self.enemies.clear()
        self.bombs.clear()
        self.explosions.clear()
        self.powerups.clear()
        self.state = "settings"


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
