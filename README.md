# PythonArcade

A collection of simple Pygame-based games packaged under an arcade shell.

## Quick Start

1. Download the repository (either clone it over HTTPS or grab the ZIP archive from GitHub and unzip it locally).
2. Install dependencies and create the virtual environment:

   ```sh
   # Linux
   bash scripts/install_linux.sh

   # Windows (Command Prompt)
   scripts\install_windows.bat
   ```

3. Launch the arcade:

   ```sh
   # Linux
   bash scripts/run_linux.sh

   # Windows
   scripts\run_windows.bat
   ```

## Updating

To pull the latest changes and refresh dependencies without losing your saves or
configuration, run the update script for your platform:

```sh
# Linux
bash scripts/update_linux.sh

# Windows
scripts\update_windows.bat
```

## Troubleshooting

- Ensure Python 3.10 or newer is installed and on your `PATH`.
- On Linux a graphical environment is required. If you see `pygame.error: No available video device`,
  install SDL libraries or run with `SDL_VIDEODRIVER=dummy`.
- Updating graphics drivers often fixes window creation or performance issues.
- Gameplay and menu activity is logged to `arcade.log` in the save directory
  (`~/.local/share/PythonArcade` on Linux/macOS, `%APPDATA%\PythonArcade` on
  Windows). Check this file for error details if a game fails to load or crashes.

## Development & Testing

Contributions are welcome. To verify your changes locally:

1. Install development dependencies:

   ```sh
   pip install -r requirements-dev.txt
   ```

2. Run linters and compile-time checks:

   ```sh
   ruff check .
   black --check .
   python -m compileall .
   ```

3. Execute the test suite:

   ```sh
   pytest
   ```

## Linux prerequisites

The Linux install script automatically detects the system package manager and
installs the SDL dependencies required by Pygame. If you would rather perform
the setup manually, install the same packages with the commands below.

### Mint/Ubuntu/Debian

```sh
sudo apt-get install python3-venv python3-pip libsdl2-dev libsdl2-image-dev \
    libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev libportmidi-dev
```

### Arch Linux

```sh
sudo pacman -S python python-pip python-virtualenv sdl2 sdl2_image sdl2_mixer \
    sdl2_ttf portmidi freetype2
```

## One-shot fix

For a quick setup, run the fix script for your platform:

```sh
# Linux
bash scripts/fix.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File scripts/fix.ps1
```

## Branch protection

In GitHub settings, enable branch protection and require the `all_green`
status check to pass before merging pull requests.

## Games

Currently included:

- Collect Dots – move the square to grab randomly spawning dots.
- TETROID – Matrix-themed Tetris clone with falling code backdrop and
  persistent high score tracking.
- Wyrm – Centipede-like shooter with splitting segments and rune blocks.
- Virus – Matrix-themed Dr. Mario-style pill matcher.
- Kart 8-Bit – retro-inspired split-screen kart racer. WASD or arrow keys to steer,
  Shift/Right Ctrl to boost, Tab to swap splitscreen.
- [Bomberman (Matrix)](pyarcade/games/bomberman/README.md) – drop bombs to clear paths
  and defeat foes. Arrow keys/WASD to move, Space/Left Shift to plant bombs.

Contributions and new mini-games are welcome!
