import pygame

from ..ui.layout import scale
from .theme import ACCENT_COLOR, PRIMARY_COLOR, draw_text


class PauseMenu:
    """Reusable pause menu handling keyboard and gamepad input."""

    def __init__(self, options: list[str], font_size: int = 32):
        self.options = options
        self.font_size = scale(font_size)
        self.index = 0
        self.normal_color = ACCENT_COLOR
        self.highlight_color = PRIMARY_COLOR

    def handle_keyboard(self, event: pygame.event.Event) -> str | None:
        if event.type != pygame.KEYDOWN:
            return None
        if event.key in (pygame.K_UP, pygame.K_w):
            self.index = (self.index - 1) % len(self.options)
        elif event.key in (pygame.K_DOWN, pygame.K_s):
            self.index = (self.index + 1) % len(self.options)
        elif event.key == pygame.K_RETURN:
            return self.options[self.index]
        elif event.key == pygame.K_ESCAPE:
            return "Resume"
        return None

    def handle_gamepad(self, event: pygame.event.Event) -> str | None:
        if event.type in (pygame.JOYAXISMOTION, pygame.JOYHATMOTION):
            if event.type == pygame.JOYHATMOTION:
                _, y = event.value
                vert = -y
            else:
                if event.axis != 1:
                    return None
                vert = event.value
            if vert < -0.5 or vert == -1:
                self.index = (self.index - 1) % len(self.options)
            elif vert > 0.5 or vert == 1:
                self.index = (self.index + 1) % len(self.options)
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button == 0:
                return self.options[self.index]
            elif event.button in (1, 7, 9):
                return "Resume"
        return None

    def draw(self, surface: pygame.surface.Surface) -> None:
        width, height = surface.get_size()
        for i, option in enumerate(self.options):
            color = self.highlight_color if i == self.index else self.normal_color
            prefix = "> " if i == self.index else "  "
            draw_text(
                surface,
                f"{prefix}{option}",
                (width // 2, height // 2 + i * self.font_size),
                self.font_size,
                color,
                center=True,
            )
