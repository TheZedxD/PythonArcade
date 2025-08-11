import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")  # fallback set below if needed
# Ensure package root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
try:
    import pygame
except Exception as e:
    # allow CI to show a clear error
    raise AssertionError(f"Pygame import failed: {e}") from e


def test_headless_boot():
    # Fallback to 'null' if 'dummy' not available
    try:
        pygame.display.init()
        pygame.display.set_mode((1, 1))
    except pygame.error:
        os.environ["SDL_VIDEODRIVER"] = "null"
        pygame.display.init()
        pygame.display.set_mode((1, 1))
    # Import app entry; adapt if main changes
    # Try package first (after rename to pyarcade)
    mod = None
    try:
        import importlib

        mod = importlib.import_module("pyarcade.main")
    except Exception:
        try:
            import importlib

            mod = importlib.import_module("pyarcade")
        except Exception as e:
            raise AssertionError(f"Could not import launcher: {e}") from e
    # Tick one frame if run() exists; otherwise just ensure import worked
    if hasattr(mod, "run"):
        pygame.event.pump()
    pygame.display.quit()
    pygame.quit()
