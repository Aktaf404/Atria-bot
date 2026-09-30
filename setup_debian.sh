#!/bin/bash
# Setup script for Debian 12 (Bookworm)

set -e

echo "==========================================="
echo "   Setup Atria-asi.ai Auto-Login (Debian)"
echo "==========================================="

echo "[1/4] Updating packages and installing system dependencies..."
sudo apt-get update
# Dependencies for Playwright / Camoufox (headless browser)
sudo apt-get install -y python3-pip python3-venv xvfb libnss3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libasound2 \
    libpango-1.0-0 libcairo2 libx11-xcb1 libxss1

echo "[2/4] Setting up Python Virtual Environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

echo "[3/4] Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Fetching Camoufox browser binaries..."
python -m camoufox fetch

echo "==========================================="
echo "Setup complete!"
echo "Please fill in 'akun.txt' with your accounts,"
echo "then start the script using: ./run.sh"
echo "==========================================="
