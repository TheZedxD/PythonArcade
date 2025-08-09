#!/usr/bin/env python3
"""Generate simple 8-bit style placeholder sprites.

The script creates small PNG images with blocky stripes and saves them
under ``assets/generated``.  These files are optional; the game falls back
to primitive shapes if they are missing.
"""
from __future__ import annotations

import os
from pathlib import Path

# Prefer Pillow if available, otherwise use pygame.
try:
    from PIL import Image, ImageDraw  # type: ignore

    USE_PIL = True
except Exception:  # pragma: no cover - Pillow not installed
    USE_PIL = False

if not USE_PIL:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame

    pygame.init()

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "assets" / "generated"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def make_striped_block(
    size: tuple[int, int],
    colors: tuple[tuple[int, int, int], tuple[int, int, int]],
    stripe: int = 4,
):
    """Create a surface/image filled with stripes."""
    if USE_PIL:
        img = Image.new("RGBA", size, colors[0])
        draw = ImageDraw.Draw(img)
        for x in range(0, size[0], stripe * 2):
            draw.rectangle((x, 0, x + stripe - 1, size[1]), fill=colors[1])
        return img
    else:  # pragma: no cover - exercised when Pillow not present
        surf = pygame.Surface(size)
        surf.fill(colors[0])
        for x in range(0, size[0], stripe * 2):
            pygame.draw.rect(surf, colors[1], (x, 0, stripe, size[1]))
        return surf


SPRITES = [
    ("car_blue.png", (32, 32), ((0, 0, 255), (255, 255, 255))),
    ("car_red.png", (32, 32), ((255, 0, 0), (255, 255, 255))),
    ("boost.png", (16, 16), ((255, 255, 0), (255, 255, 255))),
    ("oil.png", (16, 16), ((0, 0, 0), (80, 80, 80))),
    ("shell.png", (16, 16), ((255, 0, 0), (255, 255, 255))),
]


for name, size, colors in SPRITES:
    img = make_striped_block(size, colors)
    path = OUTPUT_DIR / name
    if USE_PIL:
        img.save(path)
    else:  # pragma: no cover - Pillow not present
        pygame.image.save(img, path)

if not USE_PIL:
    pygame.quit()

print(f"Generated {len(SPRITES)} placeholder images in {OUTPUT_DIR}")
