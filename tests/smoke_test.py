"""Basic smoke tests for the arcade launcher."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def test_launch_import_and_quit() -> None:
    """Import launcher modules and open a window without blocking."""

    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    arcade_dir = Path(__file__).resolve().parents[1] / "arcade"
    sys.path.append(str(arcade_dir))

    import main  # noqa: F401  # imported for side effects
    import arcade_menu  # noqa: F401
    import pygame

    pygame.display.init()
    pygame.display.set_mode((1, 1))
    pygame.display.flip()
    pygame.display.quit()
    pygame.quit()
