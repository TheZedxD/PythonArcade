#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Determine repository URL and branch
REPO_URL="${1:-$(git -C "$ROOT" config --get remote.origin.url 2>/dev/null || true)}"
if [ -z "$REPO_URL" ]; then
  echo "Could not determine repository URL. Pass it as the first argument." >&2
  exit 1
fi

if [ -n "${2:-}" ]; then
  BRANCH="$2"
else
  BRANCH=$(git -C "$ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true)
  if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
    BRANCH=$(git -C "$ROOT" remote show origin 2>/dev/null | awk '/HEAD branch/ {print $NF}')
  fi
  BRANCH=${BRANCH:-main}
fi

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

echo "Downloading latest files from $REPO_URL ($BRANCH)..."
git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$TMP_DIR/repo" >/dev/null

echo "Copying files into place..."
rsync -a --delete \
  --exclude '.git/' \
  --exclude 'scripts/update_linux.sh' \
  "$TMP_DIR/repo/" "$ROOT/"

echo "Update complete."
