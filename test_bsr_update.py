#!/usr/bin/env python3
"""
Script de testare manuală pentru actualizarea BSR-ului
Simulează procesul zilnic de actualizare pas cu pas
"""
import sys
import time
from datetime import datetime
import pytz
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config

def test_bsr_update():
    """Testează actualizarea BSR-ului pas cu pas"""
    
    print("=" * 60)
    print("🧪 TESTARE MANUALĂ ACTUALIZARE BSR")
    print("=" * 60)
    print()
    
    # Pasul 1: Conectare la Google Sheets
    print("📋 PASUL 1: Conectare la Google Sheets...")
    try:
        sheets_manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        print("✅ Conectat cu succes la Google Sheets")
    except Exception as e:
        print(f"❌ Eroare la conectare: {e}")
        return False
    print()
    
    # Pasul 2: Citire cărți din Google Sheets
    print("📚 PASUL 2: Citire cărți din Google Sheets...")
    try:
        books = sheets_manager.get_all_books()
        if not books:
            print("⚠️  Nu s-au găsit cărți în Google Sheets")
            return False
        print(f"✅ Găsite {len(books)} cărți")
        print()
        print("Primele 5 cărți:")
        for i, book in enumerate(books[:5], 1):
            print(f"  {i}. {book['name']} - {book['author']}")
            print(f"     Link: {book['amazon_link']}")
            print(f"     Coloană: {book['col']}")
            print()
    except Exception as e:
        print(f"❌ Eroare la citire cărți: {e}")
        return False
    
    # Pasul 3: Găsire rând pentru ziua curentă
    print("📅 PASUL 3: Găsire rând pentru ziua curentă...")
    try:
        today_row = sheets_manager.get_today_row()
        print(f"✅ Rândul pentru astăzi: {today_row}")
        print(f"   Data: {datetime.now(pytz.timezone('Europe/Bucharest')).strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"❌ Eroare la găsire rând: {e}")
        return False
    print()
    
    # Pasul 4: Inițializare scraper Amazon
    print("🛒 PASUL 4: Inițializare scraper Amazon...")
    try:
        amazon_scraper = AmazonScraper(
            delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
            retry_attempts=config.AMAZON_RETRY_ATTEMPTS
        )
        print("✅ Scraper Amazon inițializat")
        print(f"   Delay între request-uri: {config.AMAZON_DELAY_BETWEEN_REQUESTS}s")
        print(f"   Retry attempts: {config.AMAZON_RETRY_ATTEMPTS}")
    except Exception as e:
        print(f"❌ Eroare la inițializare scraper: {e}")
        return False
    print()
    
    # Pasul 5: Testare pe TOATE cărțile
    print("=" * 60)
    print(f"🔄 PASUL 5: Actualizare BSR pentru TOATE cărțile ({len(books)} cărți)...")
    print("=" * 60)
    print()
    
    test_books = books  # Procesăm TOATE cărțile
    success_count = 0
    failure_count = 0
    
    for idx, book in enumerate(test_books, 1):
        print(f"📖 Carte {idx}/{len(test_books)}: {book['name']}")
        print(f"   Autor: {book['author']}")
        print(f"   URL: {book['amazon_link']}")
        print(f"   Coloană în Sheet: {book['col']}")
        print()
        
        # Extragere BSR
        print("   🔍 Extragere BSR de pe Amazon...")
        try:
            bsr = amazon_scraper.extract_bsr(book['amazon_link'])
            
            if bsr:
                print(f"   ✅ BSR extras: #{bsr:,}")
                
                # Scriere în Google Sheets
                print(f"   📝 Scriere în Google Sheets (coloana {book['col']}, rândul {today_row})...")
                sheets_manager.update_bsr(book['col'], today_row, bsr)
                print(f"   ✅ BSR scris cu succes în Google Sheets!")
                success_count += 1
            else:
                print(f"   ⚠️  BSR nu a putut fi extras")
                failure_count += 1
                
        except Exception as e:
            print(f"   ❌ Eroare: {e}")
            failure_count += 1
        
        print()
        
        # Delay între cărți (dacă nu e ultima)
        if idx < len(test_books):
            print(f"   ⏳ Așteptare {config.AMAZON_DELAY_BETWEEN_REQUESTS}s între request-uri...")
            time.sleep(config.AMAZON_DELAY_BETWEEN_REQUESTS)
            print()
    
    # Rezumat final
    print("=" * 60)
    print("📊 REZUMAT FINAL")
    print("=" * 60)
    print(f"✅ Succese: {success_count}")
    print(f"❌ Eșecuri: {failure_count}")
    print(f"📚 Total procesate: {len(test_books)}")
    print()
    
    if success_count > 0:
        print("🎉 Testare reușită! BSR-urile au fost actualizate în Google Sheets.")
        print(f"   Verifică Google Sheet-ul la coloana {test_books[0]['col']}, rândul {today_row}")
    else:
        print("⚠️  Niciun BSR nu a putut fi actualizat. Verifică log-urile pentru detalii.")
    
    print()
    return success_count > 0


if __name__ == '__main__':
    print()
    print("⚠️  ATENȚIE: Acest script va scrie date reale în Google Sheets!")
    print("   Va actualiza BSR-ul pentru TOATE cărțile din Google Sheets.")
    print()
    response = input("Continuă? (da/nu): ").strip().lower()
    
    if response in ['da', 'yes', 'y', 'd']:
        print()
        success = test_bsr_update()
        sys.exit(0 if success else 1)
    else:
        print("❌ Testare anulată.")
        sys.exit(0)

