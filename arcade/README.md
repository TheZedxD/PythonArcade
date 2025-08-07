# Arcade

Simple Pygame state-driven arcade shell.

## Installation

### Unix
```
./install.sh
```

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

## Adding games

Create a new folder under `games/` with a `game.py` defining a state
class derived from `State`. The folder name becomes the menu entry.
