#!/bin/bash

# Pastikan virtual environment aktif
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment tidak ditemukan."
    echo "Harap jalankan ./setup_debian.sh terlebih dahulu."
    exit 1
fi

echo "==========================================="
echo "   Menjalankan Step 1: Login & Get Key"
echo "==========================================="
# Gunakan xvfb-run jika ingin menjalankan browser dengan GUI (headed) di server tanpa monitor.
# Karena script menggunakan headless=True, xvfb opsional, tetapi disediakan untuk berjaga-jaga
# bila browser tetap membutuhkan display.
xvfb-run -a python astra_glogin.py

echo ""
echo "==========================================="
echo "   Menjalankan Step 2: Inject ke 9Router"
echo "==========================================="
python inject_9router.py

echo ""
echo "Selesai!"
