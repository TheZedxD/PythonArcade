# Arcade

Simple Pygame state-driven arcade shell.

## Installation

### Unix
```
./install.sh
```

The script also detects Raspberry Pi OS and will prompt you to ensure SDL
drivers are installed. A graphical environment is required; running headless
on a Pi will fail because Pygame needs a display.

### Windows
```
install.bat
```

If you see errors about missing SDL libraries on Linux, ensure the
development packages are installed (e.g. `libsdl2-dev`, `libsdl2-image-dev`,
`libsdl2-mixer-dev`, `libsdl2-ttf-dev`). On Windows, missing DLL errors are
usually resolved by installing the [Microsoft Visual C++ Redistributable
package](https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist).

## Running

```
python main.py
```

Press `F11` to toggle fullscreen. The **Settings** menu accessed from the main
menu lets you switch window mode and adjust master volume. Changes persist to
`settings.json`.

## Included games

* **Collect Dots** – move the square to grab randomly spawning dots.
* **TETROID** – a Matrix-themed Tetris clone with falling code backdrop and
  persistent high score tracking.
* **Wyrm** – Centipede-like shooter with splitting segments and rune blocks.
* **Virus** – Dr. Mario-inspired pill matcher dressed in Matrix aesthetics.
* **Bomberman (Matrix)** – grid-based bomb-dropper. Arrow keys/WASD to move,
  Space/Left Shift to plant bombs.

## Adding games

Create a new folder under `games/` with a `game.py` defining a state
class derived from `State`. The folder name becomes the menu entry.
