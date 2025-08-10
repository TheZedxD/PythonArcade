import pygame

# Matrix-style color palette
BG_COLOR = (0, 0, 0)
PRIMARY_COLOR = (0, 255, 0)
ACCENT_COLOR = (0, 155, 0)


def get_font(size: int, bold: bool = False) -> pygame.font.Font:
    """Return a Courier font at the given *size*.

    All arcade games use the same monospace font to maintain the
    terminal-style aesthetic.
    """
    return pygame.font.SysFont("Courier", size, bold=bold)


def draw_text(
    surface: pygame.surface.Surface,
    text: str,
    pos: tuple[int, int],
    size: int,
    color: tuple[int, int, int] = PRIMARY_COLOR,
    *,
    bold: bool = False,
    center: bool = False,
) -> pygame.rect.Rect:
    """Draw *text* to *surface* using the shared font and colors.

    Parameters
    ----------
    surface:
        The target surface.
    text:
        Text string to render.
    pos:
        Position of the text.  Interpreted as the centre if *center* is
        true, otherwise the top-left corner.
    size:
        Font size.
    color:
        RGB text colour.
    bold:
        Whether to render in bold.
    center:
        Whether *pos* is treated as the centre point.

    Returns the rectangle of the rendered text.
    """
    font = get_font(size, bold=bold)
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(text_surf, rect)
    return rect


def terminal_panel(
    surface: pygame.surface.Surface,
    rect: pygame.rect.Rect,
    *,
    border_color: tuple[int, int, int] = ACCENT_COLOR,
    fill_color: tuple[int, int, int] | None = None,
    border_width: int = 2,
) -> None:
    """Draw a simple terminal-style panel.

    If *fill_color* is provided the rectangle is filled before drawing the
    border.
    """
    if fill_color is not None:
        pygame.draw.rect(surface, fill_color, rect)
    pygame.draw.rect(surface, border_color, rect, border_width)
