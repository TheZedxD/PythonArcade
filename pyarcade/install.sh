#!/bin/sh
set -e

# Detect Raspberry Pi to provide additional guidance
if uname -a | grep -qi "raspberry"; then
    echo "Detected Raspberry Pi – ensure you have SDL drivers installed"
fi

if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3-venv python3-dev libsdl2-dev libsdl2-image-dev \
        libsdl2-mixer-dev libsdl2-ttf-dev
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python python-pip sdl2 sdl2_image sdl2_mixer sdl2_ttf
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-devel python3-virtualenv \
        SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel
elif command -v brew >/dev/null 2>&1; then
    brew install python@3 sdl2 sdl2_image sdl2_mixer sdl2_ttf
fi

python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cat > run.sh <<'EOF'
#!/bin/sh
if [ -z "$DISPLAY" ]; then
    echo "A graphical display is required to run the arcade."
    exit 1
fi
. "$(dirname "$0")/venv/bin/activate"
python "$(dirname "$0")/main.py"
EOF
chmod +x run.sh
