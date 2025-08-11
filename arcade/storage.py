from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

APP_NAME = "pythonarcade"

def get_save_dir(app_name: str = APP_NAME) -> Path:
    """Return a platform-appropriate save directory and ensure it exists."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    path = base / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path

def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent)
    with os.fdopen(fd, "w", encoding="utf-8") as tmp:
        tmp.write(data)
    os.replace(tmp_path, path)

def save_json(path: str | Path, data: Any) -> None:
    """Save *data* to *path* as JSON using an atomic write."""
    p = Path(path)
    _atomic_write(p, json.dumps(data, indent=2))

def load_json(path: str | Path, default: Any) -> Any:
    """Load JSON from *path* or return a copy of *default* if it fails."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return copy.deepcopy(default)

__all__ = ["get_save_dir", "save_json", "load_json"]
