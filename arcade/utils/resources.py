"""Helper functions for resolving asset and save file paths."""

from __future__ import annotations

import os
import sys
from pathlib import Path


# Base directory of the project (the ``arcade`` package root).
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def asset_path(*parts: str) -> Path:
    """Return an absolute path inside the project for the given *parts*."""

    return PROJECT_ROOT.joinpath(*parts)


def _platform_base() -> Path:
    """Return the OS-specific base directory for persistent data."""

    if sys.platform.startswith("win"):
        base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path.home() / ".local" / "share"
    return base / "PythonArcade"


def get_save_dir() -> Path:
    """Ensure and return the directory used for saving user data."""

    path = _platform_base()
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_path(*parts: str) -> Path:
    """Return a path within the persistent save directory."""

    return get_save_dir().joinpath(*parts)


__all__ = ["asset_path", "get_save_dir", "save_path"]
