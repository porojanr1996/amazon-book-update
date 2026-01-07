#!/usr/bin/env python3
"""
Test simplu pentru scrierea în Google Sheets
"""
from google_sheets_transposed import GoogleSheetsManager
import config
from datetime import datetime

print("🧪 Test scriere în Google Sheets")
print("=" * 50)

# Conectare
sheets_manager = GoogleSheetsManager(
    config.GOOGLE_SHEETS_CREDENTIALS_PATH,
    config.GOOGLE_SHEETS_SPREADSHEET_ID
)

# Citire cărți
books = sheets_manager.get_all_books()
print(f"✅ Găsite {len(books)} cărți")
print()

if not books:
    print("❌ Nu sunt cărți în Google Sheets")
    exit(1)

# Test cu prima carte
book = books[0]
print(f"📖 Test cu: {book['name']}")
print(f"   Coloană: {book['col']}")
print()

# Găsire rând pentru astăzi
today_row = sheets_manager.get_today_row()
print(f"📅 Rând pentru astăzi: {today_row}")
print()

# Test scriere cu valoare simulată
test_bsr = 12345
print(f"✍️  Scriere BSR simulat: {test_bsr}")
print(f"   Coloană: {book['col']}, Rând: {today_row}")

try:
    sheets_manager.update_bsr(book['col'], today_row, test_bsr)
    print("✅ BSR scris cu succes în Google Sheets!")
    print()
    print("🎉 Test reușit! Verifică Google Sheet-ul pentru a vedea valoarea.")
except Exception as e:
    print(f"❌ Eroare la scriere: {e}")
    exit(1)

