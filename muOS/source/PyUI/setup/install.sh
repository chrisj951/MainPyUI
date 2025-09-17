#!/bin/sh
set -e  # Exit immediately if a command fails

# Path to the marker file (next to this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MARKER_FILE="$SCRIPT_DIR/.offline_install_done"

# If the marker file exists, skip everything
if [ -f "$MARKER_FILE" ]; then
    echo "Offline installation already completed. Skipping."
    exit 0
fi

# Step 1: Install pip, setuptools, and wheel completely offline
python3 pip_offline/pip-25.2-py3-none-any.whl/pip install --no-index --find-links=pip_offline pip setuptools wheel || \
python3 -m pip install --no-index --find-links=pip_offline pip setuptools wheel

# Step 2: Use pip via python to install your project dependencies
python3 -m pip install --no-index --find-links=offline_packages psutil pyserial pillow pysdl2

echo "Offline installation completed successfully!"

#mkdir -p /mnt/sdcard/pyui/logs
#mkdir -p /mnt/sdcard/Saves

mkdir -p /mnt/mmc/MUOS/log/pyui/

# Create symlink if it doesn't exist
#if [ ! -L /mnt/SDCARD ]; then
#    ln -s /mnt/sdcard /mnt/SDCARD
#fi

touch "$MARKER_FILE"
