#!/usr/bin/env bash
set -euo pipefail

# Detect and install system packages (Mint/Ubuntu vs Arch)
if command -v apt >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y python3-venv python3-pip \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libfreetype6-dev libportmidi-dev
elif command -v pacman >/dev/null 2>&1; then
  sudo pacman -Syu --noconfirm
  sudo pacman -S --needed --noconfirm \
    python python-pip python-virtualenv \
    sdl2 sdl2_image sdl2_mixer sdl2_ttf portmidi freetype2
fi

# Create venv & install deps
python3 -m venv .venv || python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -U pip
pip install -r requirements.txt || true
pip install -r requirements-dev.txt

# Lint/format, compile, test (headless)
ruff check --fix .
black .
python -m compileall -q -f .
export SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-dummy}
pytest -q

echo "Fix complete."
