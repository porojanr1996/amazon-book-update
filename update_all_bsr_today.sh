#!/bin/bash
# Script pentru actualizarea BSR-ului pentru toate worksheet-urile cu data de azi

echo "🔄 Actualizare BSR pentru toate worksheet-urile..."
echo ""

cd /home/ec2-user/app/books-reporting || exit 1

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează update-ul pentru toate worksheet-urile
echo "📚 Rulează update BSR pentru toate worksheet-urile..."
python3 update_bsr.py --all

echo ""
echo "✅ Actualizare completă!"
echo "📊 Graficele se vor actualiza automat când se reîncarcă pagina."

