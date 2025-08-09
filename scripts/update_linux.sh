#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# Stash or warn about local changes
if ! git diff-index --quiet HEAD --; then
  echo "Stashing local changes..."
  git stash push --include-untracked -m "pre-update-$(date +%s)"
  echo "Local changes stashed. Use 'git stash pop' after the update to restore them."
fi

DEFAULT_BRANCH=$(git remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
DEFAULT_BRANCH=${DEFAULT_BRANCH:-main}

echo "Pulling latest from $DEFAULT_BRANCH..."
git pull --rebase origin "$DEFAULT_BRANCH"

# Preserve user data
timestamp=$(date +%s)
for d in save config; do
  if [ -d "$ROOT/$d" ]; then
    cp -r "$ROOT/$d" "$ROOT/${d}_backup_$timestamp"
  fi
done

# Activate virtual environment
if [ -d "$ROOT/.venv" ]; then
  . "$ROOT/.venv/bin/activate"
else
  echo ".venv not found. Please run scripts/install_linux.sh first." >&2
  exit 1
fi

python -m pip install -r "$ROOT/requirements.txt"

# Run migrations if available
if [ -f "$ROOT/scripts/migrate_user_data.py" ]; then
  python "$ROOT/scripts/migrate_user_data.py"
fi

if [ -z "$DISPLAY" ]; then
  export SDL_VIDEODRIVER=${SDL_VIDEODRIVER:-dummy}
  export SDL_AUDIODRIVER=${SDL_AUDIODRIVER:-dummy}
fi

if ! python -m pytest "$ROOT/tests/smoke_test.py"; then
  echo "Smoke test failed. Please check logs." >&2
  exit 1
fi

echo "Update complete."
