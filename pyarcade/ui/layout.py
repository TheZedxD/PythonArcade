"""Screen scaling helpers."""

from __future__ import annotations

REFERENCE_RES = (1280, 720)
_scale = 1.0


def init(size: tuple[int, int]) -> None:
    """Initialise the scaling factor based on *size*."""

    global _scale
    _scale = min(size[0] / REFERENCE_RES[0], size[1] / REFERENCE_RES[1])


def scale(value: int | float) -> int:
    """Scale *value* relative to the reference resolution."""

    return int(value * _scale)


__all__ = ["init", "scale"]
