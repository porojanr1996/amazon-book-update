#!/bin/bash

# Script pentru pornirea website-ului
cd "$(dirname "$0")"
source venv/bin/activate
python app.py

