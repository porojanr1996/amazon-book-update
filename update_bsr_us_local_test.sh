#!/bin/bash
# Script pentru test local cu delay redus și browser vizibil

echo "============================================================"
echo "🔄 TEST LOCAL BSR UPDATE (HEADED MODE, FAST DELAYS)"
echo "============================================================"
echo ""

cd "$(dirname "$0")" || exit 1

# Activează venv dacă există
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

# Setează headless=false și delay-uri mici pentru test
export PLAYWRIGHT_HEADLESS=false
export AMAZON_DELAY_MIN=2
export AMAZON_DELAY_MAX=5

echo "📚 Rulează update BSR pentru Crime Fiction - US..."
echo "   Delay: 2-5 secunde (pentru test)"
echo "   Browser: Vizibil (headed mode)"
echo ""
echo "da" | python3 update_bsr.py --worksheet "Crime Fiction - US" --dry-run

echo ""
echo "✅ Test complet!"

