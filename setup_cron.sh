#!/bin/bash

# Script pentru setup automat al cron job-ului
# Rulează: ./setup_cron.sh

echo "=========================================="
echo "Setup Cron Job pentru BSR Scraper"
echo "=========================================="
echo ""

# Obține path-ul absolut al scriptului
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRON_SCRIPT="$SCRIPT_DIR/cron_scraper.sh"

# Verifică dacă scriptul există
if [ ! -f "$CRON_SCRIPT" ]; then
    echo "❌ Eroare: cron_scraper.sh nu a fost găsit!"
    exit 1
fi

# Face scriptul executabil
chmod +x "$CRON_SCRIPT"
echo "✓ Script cron_scraper.sh este executabil"

# Creează linia pentru cron (10:00 AM zilnic, Bucharest time)
CRON_LINE="0 10 * * * $CRON_SCRIPT"

# Verifică dacă cron job-ul există deja
if crontab -l 2>/dev/null | grep -q "$CRON_SCRIPT"; then
    echo "⚠️  Cron job-ul există deja!"
    echo ""
    echo "Cron job-urile existente:"
    crontab -l | grep -v "^#" | grep -v "^$"
    echo ""
    read -p "Vrei să-l ștergi și să-l adaugi din nou? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Șterge cron job-ul vechi
        crontab -l 2>/dev/null | grep -v "$CRON_SCRIPT" | crontab -
        echo "✓ Cron job vechi șters"
    else
        echo "❌ Anulat. Cron job-ul rămâne neschimbat."
        exit 0
    fi
fi

# Adaugă cron job-ul nou
(crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -

echo ""
echo "✅ Cron job adăugat cu succes!"
echo ""
echo "Detalii:"
echo "  - Rulează zilnic la: 10:00 AM"
echo "  - Script: $CRON_SCRIPT"
echo "  - Log-uri: $SCRIPT_DIR/scraper.log"
echo ""
echo "Cron job-urile active:"
crontab -l | grep -v "^#" | grep -v "^$"
echo ""
echo "Pentru a verifica log-urile:"
echo "  tail -f $SCRIPT_DIR/scraper.log"
echo ""
echo "Pentru a șterge cron job-ul:"
echo "  crontab -e"
echo "  (șterge linia cu cron_scraper.sh)"

