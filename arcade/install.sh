#!/bin/sh
set -e

if command -v apt >/dev/null 2>&1; then
    sudo apt update
    sudo apt install -y python3-venv python3-dev libsdl2-dev libsdl2-image-dev \
        libsdl2-mixer-dev libsdl2-ttf-dev
elif command -v pacman >/dev/null 2>&1; then
    sudo pacman -Sy --noconfirm python python-pip sdl2 sdl2_image sdl2_mixer sdl2_ttf
elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3 python3-devel python3-virtualenv \
        SDL2-devel SDL2_image-devel SDL2_mixer-devel SDL2_ttf-devel
fi

python3 -m venv venv
. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cat > run.sh <<'EOF'
#!/bin/sh
. "$(dirname "$0")/venv/bin/activate"
python "$(dirname "$0")/main.py"
EOF
chmod +x run.sh
