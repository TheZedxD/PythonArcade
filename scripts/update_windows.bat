@echo off
setlocal
set ROOT=%~dp0..
cd /d "%ROOT%"

for /f "delims=" %%i in ('git status --porcelain') do set DIRTY=1
if defined DIRTY (
  echo Stashing local changes...
  git stash push --include-untracked -m "pre-update-%DATE%_%TIME%"
  echo Local changes stashed. Run "git stash pop" after the update to restore them.
)

for /f "tokens=3" %%i in ('git remote show origin ^| findstr /c:"HEAD branch"') do set DEFAULT_BRANCH=%%i
if "%DEFAULT_BRANCH%"=="" set DEFAULT_BRANCH=main

echo Pulling latest from %DEFAULT_BRANCH%...
git pull --rebase origin %DEFAULT_BRANCH%

set TIMESTAMP=%RANDOM%
for %%d in (save config) do (
  if exist "%ROOT%\%%d" (
    xcopy "%ROOT%\%%d" "%ROOT%\%%d_backup_%TIMESTAMP%" /E /I /Y >nul
  )
)

if not exist "%ROOT%\.venv" (
  echo .venv not found. Please run scripts\install_windows.bat first.
  exit /b 1
)

call "%ROOT%\.venv\Scripts\activate"

python -m pip install -r "%ROOT%\requirements.txt"

if exist "%ROOT%\scripts\migrate_user_data.py" (
  python "%ROOT%\scripts\migrate_user_data.py"
)

if not defined DISPLAY (
  set SDL_VIDEODRIVER=dummy
  set SDL_AUDIODRIVER=dummy
)

python -m pytest "%ROOT%\tests\smoke_test.py"
if errorlevel 1 (
  echo Smoke test failed. Please check logs.
  exit /b 1
)

echo Update complete.
