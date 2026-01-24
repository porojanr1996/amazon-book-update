#!/bin/bash
# Script pentru actualizarea BSR-ului doar pentru Crime Fiction - US

echo "============================================================"
echo "🔄 ACTUALIZARE BSR PENTRU CRIME FICTION - US"
echo "============================================================"
echo ""

# Navighează la directorul proiectului
cd "$(dirname "$0")" || exit 1

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează update-ul pentru US
echo "📚 Rulează update BSR pentru Crime Fiction - US..."
echo ""
echo "da" | python3 update_bsr.py --worksheet "Crime Fiction - US"

echo ""
echo "============================================================"
echo "✅ Actualizare completă pentru Crime Fiction - US!"
echo "============================================================"
echo ""
echo "📊 Graficele se vor actualiza automat când se reîncarcă pagina."
echo ""
