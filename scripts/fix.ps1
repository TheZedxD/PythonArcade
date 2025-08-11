Param()
$ErrorActionPreference = "Stop"
if (!(Test-Path .venv)) { py -m venv .venv }
.\.venv\Scripts\python -m pip install -U pip
.\.venv\Scripts\pip install -r requirements.txt 2>$null
.\.venv\Scripts\pip install -r requirements-dev.txt
.\.venv\Scripts\python -m ruff check --fix .
.\.venv\Scripts\python -m black .
.\.venv\Scripts\python -m compileall -q -f .
if (-not $env:SDL_VIDEODRIVER) { $env:SDL_VIDEODRIVER = "dummy" }
.\.venv\Scripts\pytest -q
Write-Host "Fix complete."
