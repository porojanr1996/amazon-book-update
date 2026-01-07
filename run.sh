#!/bin/bash

# Script pentru rulare simplă a scraper-ului
# Utilizare: ./run.sh

cd "$(dirname "$0")"

# Activează virtual environment dacă există
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Rulează scraper-ul
python3 daily_scraper.py

