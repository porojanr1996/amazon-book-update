#!/bin/bash
# Script care rulează update BSR și apoi re-încearcă pentru cărțile eșuate

echo "🔄 Actualizare BSR pentru toate worksheet-urile..."
echo ""

cd /home/ec2-user/app/books-reporting || exit 1

# Setează variabilele de mediu pentru credentials
export GOOGLE_SHEETS_CREDENTIALS_PATH=/home/ec2-user/app/books-reporting/credentials.json
export GOOGLE_SHEETS_SPREADSHEET_ID=1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează update-ul inițial pentru toate worksheet-urile
echo "📚 Pasul 1: Rulează update BSR pentru toate worksheet-urile..."
echo "da" | python3 update_bsr.py --all

echo ""
echo "⏳ Așteptare 5 secunde pentru finalizarea scrierii în log-uri..."
sleep 5

echo ""
echo "📋 Pasul 2: Analizare log-uri și identificare cărți eșuate..."
echo ""

# Re-încearcă pentru cărțile eșuate
echo "da" | python3 retry_failed_bsr.py --log-file app.log

echo ""
echo "✅ Proces complet finalizat!"
echo "📊 Verifică Google Sheets pentru a vedea noile valori BSR"

