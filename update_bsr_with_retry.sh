#!/bin/bash
# Script care rulează update BSR și apoi retry pentru cărțile eșuate

echo "🔄 Actualizare BSR pentru toate worksheet-urile..."
echo ""

cd /home/ec2-user/app/books-reporting || exit 1

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează update-ul inițial pentru toate worksheet-urile
echo "📚 Rulează update BSR inițial..."
echo "da" | python3 update_bsr.py --all

# Așteaptă puțin pentru ca log-urile să se scrie
sleep 5

echo ""
echo "============================================================"
echo "🔍 Verificare cărți eșuate și retry..."
echo "============================================================"
echo ""

# Rulează retry pentru cărțile eșuate
echo "da" | python3 retry_failed_bsr.py --max-retries 2

echo ""
echo "✅ Proces complet finalizat!"
echo "📊 Verifică Google Sheets pentru a vedea noile valori BSR"

