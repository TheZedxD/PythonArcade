# PythonArcade

A collection of simple Pygame-based games packaged under an arcade shell.

## Installation

From the `arcade` directory you can set up a local virtual environment and
install dependencies:

```sh
cd arcade
./install.sh   # or install.bat on Windows
```

This will create a `venv` and generate a `run.sh` (or `run.bat`) launcher.

If you already have Python and SDL dependencies installed you can instead run:

```sh
cd arcade
python -m pip install -r requirements.txt
python main.py
```

## Games

Currently included:

- Collect Dots – move the square to grab randomly spawning dots.
- TETROID – Matrix-themed Tetris clone with falling code backdrop and
  persistent high score tracking.
- Wyrm – Centipede-like shooter with splitting segments and rune blocks.

Contributions and new mini-games are welcome!
