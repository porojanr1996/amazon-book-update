#!/bin/bash
# Script pentru actualizarea BSR-ului pentru US cu browser vizibil (headed mode)

echo "============================================================"
echo "🔄 ACTUALIZARE BSR PENTRU CRIME FICTION - US (HEADED MODE)"
echo "============================================================"
echo ""

# Navighează la directorul proiectului
cd "$(dirname "$0")" || exit 1

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Setează headless=False pentru a vedea browser-ul
export PLAYWRIGHT_HEADLESS=false

# Rulează update-ul pentru US
echo "📚 Rulează update BSR pentru Crime Fiction - US (browser vizibil)..."
echo ""
echo "da" | python3 update_bsr.py --worksheet "Crime Fiction - US"

echo ""
echo "============================================================"
echo "✅ Actualizare completă pentru Crime Fiction - US!"
echo "============================================================"

