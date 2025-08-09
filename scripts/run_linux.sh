#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [ -z "$DISPLAY" ]; then
  export SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-dummy}
  export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
fi
. "$ROOT/.venv/bin/activate"
python "$ROOT/arcade/main.py"
