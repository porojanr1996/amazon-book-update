#!/bin/bash
# Script pentru a rula update BSR pentru un singur worksheet cu browser vizibil

if [ -z "$1" ]; then
    echo "Utilizare: $0 <worksheet_name>"
    echo "Exemplu: $0 'Crime Fiction - US'"
    exit 1
fi

WORKSHEET="$1"

echo "============================================================"
echo "🔄 UPDATE BSR PENTRU: $WORKSHEET (HEADED MODE)"
echo "============================================================"
echo ""

# Navighează la directorul proiectului
cd "$(dirname "$0")" || exit 1

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activat"
fi

# Setează headless=False pentru a vedea browser-ul
export PLAYWRIGHT_HEADLESS=false
export AMAZON_DELAY_MIN=2
export AMAZON_DELAY_MAX=5

echo "📋 Configurație:"
echo "   - Browser: Vizibil (headed mode)"
echo "   - Delay: 2-5 secunde (pentru test)"
echo "   - Worksheet: $WORKSHEET"
echo ""

# Rulează update
env PLAYWRIGHT_HEADLESS=false AMAZON_DELAY_MIN=2 AMAZON_DELAY_MAX=5 python3 update_bsr.py --worksheet "$WORKSHEET"

echo ""
echo "============================================================"
echo "✅ Update complet pentru $WORKSHEET!"
echo "============================================================"

