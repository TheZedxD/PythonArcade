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

## Running

```
python main.py
```

Press `F11` to toggle fullscreen.

## Adding games

Create a new folder under `games/` with a `game.py` defining a state
class derived from `State`. The folder name becomes the menu entry.
