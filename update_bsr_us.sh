#!/bin/bash
# Script pentru actualizarea BSR doar pentru Crime Fiction - US

echo "🔄 Actualizare BSR pentru Crime Fiction - US..."
echo ""

cd /home/ec2-user/app/books-reporting || exit 1

# Setează variabilele de mediu
export GOOGLE_SHEETS_CREDENTIALS_PATH=/home/ec2-user/app/books-reporting/credentials.json
export GOOGLE_SHEETS_SPREADSHEET_ID=1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA

# Activează environment-ul dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează update-ul pentru US
echo "📚 Pasul 1: Rulează update BSR pentru Crime Fiction - US..."
echo "da" | python3 update_bsr.py --worksheet "Crime Fiction - US"

echo ""
echo "⏳ Așteptare 5 secunde pentru finalizarea scrierii în log-uri..."
sleep 5

echo ""
echo "📋 Pasul 2: Re-încearcă pentru cărțile eșuate..."
echo "da" | python3 retry_failed_bsr.py --log-file app.log

echo ""
echo "✅ Proces complet finalizat pentru Crime Fiction - US!"

