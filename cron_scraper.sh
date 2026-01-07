#!/bin/bash

# Script pentru cron job - Scraping zilnic BSR
# Acest script rulează scraping-ul și loghează rezultatele

# Setează directorul de lucru (ajustă la path-ul tău)
cd "$(dirname "$0")"

# Activează virtual environment dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează scraper-ul și loghează output-ul
python3 daily_scraper.py >> scraper.log 2>&1

# Opțional: Trimite email dacă există erori (necesită configurare mail)
# if [ $? -ne 0 ]; then
#     echo "Scraping failed at $(date)" | mail -s "BSR Scraper Error" your-email@example.com
# fi

