#!/usr/bin/env bash
set -e

PYTHON=python3
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
if [ -d "$ROOT/.venv" ]; then
  "$PYTHON" -m venv "$ROOT/.venv" --upgrade
else
  "$PYTHON" -m venv "$ROOT/.venv"
fi

# Install Python dependencies inside the virtual environment
"$ROOT/.venv/bin/python" -m pip install --upgrade pip
"$ROOT/.venv/bin/python" -m pip install -r "$ROOT/requirements.txt" || true

# Fallback to system pygame if install failed
if ! "$ROOT/.venv/bin/python" - <<'PY' >/dev/null 2>&1
import pygame
PY
then
  if "$PYTHON" - <<'PY' >/dev/null 2>&1
import pygame
PY
  then
    SYS_SITE=$("$PYTHON" - <<'PY'
import sysconfig
print(sysconfig.get_paths()['purelib'])
PY)
    VENV_SITE=$("$ROOT/.venv/bin/python" - <<'PY'
import sysconfig
print(sysconfig.get_paths()['purelib'])
PY)
    cp -r "$SYS_SITE/pygame" "$VENV_SITE/" 2>/dev/null || true
    if [ -d "$SYS_SITE/pygame.libs" ]; then
      cp -r "$SYS_SITE/pygame.libs" "$VENV_SITE/" 2>/dev/null || true
    fi
  fi
fi

# Smoke test Pygame headlessly
SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-dummy} "$ROOT/.venv/bin/python" - <<'PY'
import os, pygame
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
