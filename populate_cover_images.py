#!/usr/bin/env python3
"""
Script pentru popularea cache-ului cu imagini cover pentru toate cărțile
"""
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
from app.services.cache_service import set_cached_cover, get_cached_cover
import config
import time

print("🖼️  POPULARE CACHE CU IMAGINI COVER")
print("=" * 60)
print()

sheets_manager = GoogleSheetsManager(
    config.GOOGLE_SHEETS_CREDENTIALS_PATH,
    config.GOOGLE_SHEETS_SPREADSHEET_ID
)

worksheets = ['Crime Fiction - US', 'Crime Fiction - UK']

scraper = AmazonScraper(
    delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
    retry_attempts=config.AMAZON_RETRY_ATTEMPTS
)

total_success = 0
total_failed = 0

for worksheet_name in worksheets:
    print(f"📚 Procesare: {worksheet_name}")
    print("-" * 60)
    
    books = sheets_manager.get_all_books(worksheet_name)
    print(f"   Găsite {len(books)} cărți")
    print()
    
    for i, book in enumerate(books, 1):
        # Verifică dacă există deja în cache
        cached = get_cached_cover(book['amazon_link'])
        if cached:
            print(f"   ✅ {i}/{len(books)} {book['name']}: Deja în cache")
            total_success += 1
            continue
        
        print(f"   🔍 {i}/{len(books)} {book['name']}...", end=' ', flush=True)
        
        try:
            cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=False)
            if not cover_url:
                # Încearcă cu Playwright
                cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=True)
            
            if cover_url:
                set_cached_cover(book['amazon_link'], cover_url)
                print(f"✅")
                total_success += 1
            else:
                print(f"❌ Nu s-a găsit")
                set_cached_cover(book['amazon_link'], None)  # Cache None pentru a evita retry-uri
                total_failed += 1
        except Exception as e:
            print(f"❌ Eroare: {e}")
            total_failed += 1
        
        # Delay între request-uri
        if i < len(books):
            time.sleep(config.AMAZON_DELAY_BETWEEN_REQUESTS)
    
    print()

print("=" * 60)
print("📊 REZUMAT:")
print(f"   ✅ Succese: {total_success}")
print(f"   ❌ Eșecuri: {total_failed}")
print(f"   📚 Total: {total_success + total_failed}")
print()
print("✅ Cache populat! Refresh-uiește pagina web pentru a vedea imaginile.")
