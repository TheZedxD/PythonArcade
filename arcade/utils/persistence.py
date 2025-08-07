import json
from pathlib import Path
from typing import Any


def save_json(path: str, data: Any) -> None:
    """Save *data* to *path* as JSON."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_json(path: str, default: Any) -> Any:
    """Load JSON data from *path* or return *default* if missing or invalid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default
