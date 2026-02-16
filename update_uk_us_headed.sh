#!/bin/bash
# Script pentru a rula update BSR pentru UK și US cu browser vizibil (headed mode)

echo "============================================================"
echo "🔄 UPDATE BSR PENTRU UK ȘI US (HEADED MODE - BROWSER VIZIBIL)"
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
echo "   - Worksheets: Crime Fiction - UK, Crime Fiction - US"
echo ""

# Confirmare
read -p "Continuă cu update-ul? (da/nu): " response
if [[ ! "$response" =~ ^[Dd][Aa]$ ]] && [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]] && [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "❌ Anulat."
    exit 0
fi

echo ""
echo "============================================================"
echo "🚀 Pornire Update pentru Crime Fiction - UK"
echo "============================================================"
echo ""

# Rulează update pentru UK
env PLAYWRIGHT_HEADLESS=false AMAZON_DELAY_MIN=2 AMAZON_DELAY_MAX=5 python3 update_bsr.py --worksheet "Crime Fiction - UK"

echo ""
echo "============================================================"
echo "🚀 Pornire Update pentru Crime Fiction - US"
echo "============================================================"
echo ""

# Rulează update pentru US
env PLAYWRIGHT_HEADLESS=false AMAZON_DELAY_MIN=2 AMAZON_DELAY_MAX=5 python3 update_bsr.py --worksheet "Crime Fiction - US"

echo ""
echo "============================================================"
echo "✅ Update complet pentru UK și US!"
echo "============================================================"

