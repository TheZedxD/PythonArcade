#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
. "$ROOT/.venv/bin/activate"
python "$ROOT/pyarcade/main.py"
