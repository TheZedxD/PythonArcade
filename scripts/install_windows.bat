@echo off
setlocal
where python >nul 2>nul || (
  echo Python 3.10+ is required.
  exit /b 1
)
set SYS_PY=python
%SYS_PY% -c "import sys; exit(0 if sys.version_info >= (3,10) else 1)" || (
  echo Python 3.10+ is required.
  exit /b 1
)
set ROOT=%~dp0..
if exist "%ROOT%\.venv" (
  %SYS_PY% -m venv "%ROOT%\.venv" --upgrade >nul
) else (
  %SYS_PY% -m venv "%ROOT%\.venv" >nul
)
call "%ROOT%\.venv\Scripts\activate"
python -m pip install --upgrade pip
python -m pip install -r "%ROOT%\requirements.txt" || set PIPFAIL=1
python -c "import pygame" >nul 2>nul || (
  %SYS_PY% -c "import pygame, shutil, sysconfig, pathlib, os; base=pathlib.Path(r'%ROOT%\\.venv')/'Lib'/'site-packages'; src=pathlib.Path(pygame.__file__).parent; shutil.copytree(src, base/'pygame', dirs_exist_ok=True); libs=src.parent/'pygame.libs';\nif libs.is_dir(): shutil.copytree(libs, base/'pygame.libs', dirs_exist_ok=True)"
)
set SDL_VIDEODRIVER=dummy
python -c "import os, pygame; os.environ.setdefault('SDL_VIDEODRIVER','dummy'); pygame.display.init(); pygame.display.set_mode((1,1), pygame.DOUBLEBUF); pygame.display.flip(); pygame.display.quit(); pygame.quit()"
echo Installation complete.
echo.
echo Next steps:
echo   1. Activate the virtual environment:
echo        call .venv\Scripts\activate
echo   2. Launch the arcade:
echo        scripts\run_windows.bat
