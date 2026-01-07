#!/usr/bin/env python3
"""
Test direct extragere imagini - forțează extragerea
"""
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
from app.services.cache_service import get_cached_cover, set_cached_cover, clear_all_caches
import config

print("🖼️  TEST DIRECT EXTRAGERE IMAGINI")
print("=" * 50)
print()

# Clear cache pentru a forța extragerea
print("🗑️  Ștergere cache...")
try:
    clear_all_caches()
    print("✅ Cache șters")
except Exception as e:
    print(f"⚠️  {e}")
print()

# Obține o carte
print("📚 Obținere carte de test...")
sheets_manager = GoogleSheetsManager(
    config.GOOGLE_SHEETS_CREDENTIALS_PATH,
    config.GOOGLE_SHEETS_SPREADSHEET_ID
)
books = sheets_manager.get_all_books('Crime Fiction - US')
book = books[0]

print(f"📖 Carte: {book['name']}")
print(f"🔗 URL: {book['amazon_link']}")
print()

# Test extragere
print("🔍 Extragere imagine...")
scraper = AmazonScraper(
    delay_between_requests=2.0,
    retry_attempts=2
)

cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=False)
if cover_url:
    print(f"✅ Cover extras: {cover_url}")
    print()
    
    # Salvează în cache
    print("💾 Salvare în cache...")
    set_cached_cover(book['amazon_link'], cover_url)
    print("✅ Salvat")
    print()
    
    # Verifică cache
    print("🔍 Verificare cache...")
    cached = get_cached_cover(book['amazon_link'])
    if cached:
        print(f"✅ Cache funcționează: {cached[:80]}...")
    else:
        print("❌ Cache nu funcționează")
else:
    print("❌ Nu s-a putut extrage cover")
    print()
    print("🔄 Încercare cu Playwright...")
    cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=True)
    if cover_url:
        print(f"✅ Cover extras cu Playwright: {cover_url}")
    else:
        print("❌ Nici cu Playwright nu s-a putut extrage")

print()
print("=" * 50)
print("✅ TEST FINALIZAT!")
