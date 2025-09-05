#!/bin/sh
set -e  # Exit immediately if a command fails

# Step 1: Install pip, setuptools, and wheel completely offline
python3 pip_offline/pip-25.2-py3-none-any.whl/pip install --no-index --find-links=pip_offline pip setuptools wheel || \
python3 -m pip install --no-index --find-links=pip_offline pip setuptools wheel

# Step 2: Use pip via python to install your project dependencies
python3 -m pip install --no-index --find-links=offline_packages psutil pyserial pillow pysdl2

echo "Offline installation completed successfully!"

mkdir -p /mnt/sdcard/pyui/logs
mkdir -p /mnt/sdcard/Saves

ln -s /mnt/sdcard /mnt/SDCARD

