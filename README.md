# PythonArcade

A collection of simple Pygame-based games packaged under an arcade shell.

## Quick Start

1. Clone this repository.
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

## Games

Currently included:

- Collect Dots – move the square to grab randomly spawning dots.
- TETROID – Matrix-themed Tetris clone with falling code backdrop and
  persistent high score tracking.
- Wyrm – Centipede-like shooter with splitting segments and rune blocks.
- Virus – Matrix-themed Dr. Mario-style pill matcher.
- Kart 8-Bit – retro-inspired split-screen kart racer. WASD or arrow keys to steer,
  Shift/Right Ctrl to boost, Tab to swap splitscreen.
- Bomberman (Matrix) – drop bombs to clear paths and defeat foes. Arrow keys/WASD to
  move, Space/Left Shift to plant bombs.

Contributions and new mini-games are welcome!
