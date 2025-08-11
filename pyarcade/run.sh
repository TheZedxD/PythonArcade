#!/bin/sh
if [ -z "$DISPLAY" ]; then
    echo "A graphical display is required to run the arcade."
    exit 1
fi
. "$(dirname "$0")/venv/bin/activate"
python "$(dirname "$0")/main.py"
