#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python3}
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python 3.10+ is required." >&2
  exit 1
fi

"$PYTHON" - <<'PY'
import sys
if sys.version_info < (3, 10):
    print("Python 3.10+ is required.", file=sys.stderr)
    sys.exit(1)
PY

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/.venv"

require_sudo() {
  if [ "$(id -u)" -eq 0 ]; then
    echo ""
    return 0
  fi
  if command -v sudo >/dev/null 2>&1; then
    echo "sudo"
    return 0
  fi
  echo "This script needs to install system packages. Re-run it as root or install 'sudo'." >&2
  exit 1
}

install_system_packages() {
  local sudo_cmd
  sudo_cmd=$(require_sudo)

  if command -v apt-get >/dev/null 2>&1; then
    $sudo_cmd apt-get update -y
    $sudo_cmd apt-get install -y \
      python3-venv python3-dev python3-pip \
      libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
      libfreetype6-dev libportmidi-dev libjpeg-dev zlib1g-dev
    return 0
  fi

  if command -v pacman >/dev/null 2>&1; then
    $sudo_cmd pacman -Syu --noconfirm
    $sudo_cmd pacman -S --needed --noconfirm \
      python python-pip python-virtualenv \
      sdl2 sdl2_image sdl2_mixer sdl2_ttf portmidi freetype2
    return 0
  fi

  if command -v dnf >/dev/null 2>&1; then
    $sudo_cmd dnf install -y \
      python3 python3-pip python3-virtualenv python3-devel \
      SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel \
      freetype-devel portmidi-devel
    return 0
  fi

  if command -v zypper >/dev/null 2>&1; then
    $sudo_cmd zypper --non-interactive refresh
    if ! $sudo_cmd zypper --non-interactive install \
      python311 python311-devel python311-pip python311-virtualenv \
      SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel \
      freetype-devel portmidi-devel; then
      echo "Automatic installation via zypper failed. Install these packages manually:" >&2
      echo "  python3-venv python3-devel python3-pip SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel freetype-devel portmidi-devel" >&2
    fi
    return 0
  fi

  echo "Unsupported package manager. Install the following packages manually:" >&2
  echo "  python3-venv python3-dev python3-pip libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev libportmidi-dev" >&2
}

install_system_packages

cd "$ROOT"

if [ -d "$VENV" ]; then
  "$PYTHON" -m venv "$VENV" --upgrade
else
  "$PYTHON" -m venv "$VENV"
fi

"$VENV/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
if [ -f "$ROOT/requirements-dev.txt" ]; then
  "$VENV/bin/python" -m pip install -r "$ROOT/requirements-dev.txt"
fi

SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-dummy} "$VENV/bin/python" - <<'PY'
import os
import pygame

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
pygame.display.init()
pygame.display.set_mode((1, 1), pygame.DOUBLEBUF)
pygame.display.flip()
pygame.display.quit()
pygame.quit()
PY

cat <<'EOS'
Installation complete.

Next steps:
  1. Activate the virtual environment:
       source .venv/bin/activate
  2. Launch the arcade:
       bash scripts/run_linux.sh
EOS
