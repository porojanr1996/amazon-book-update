#!/usr/bin/env python3
"""
Test pentru extragerea de imagini (cover images) pentru cărți
"""
import sys
from google_sheets_transposed import GoogleSheetsManager
from amazon_scraper import AmazonScraper
import config
import re

def test_extract_cover_images():
    """Testează extragerea de imagini pentru cărți"""
    
    print("=" * 60)
    print("🖼️  TEST EXTRAGERE IMAGINI COVER")
    print("=" * 60)
    print()
    
    # Conectare la Google Sheets
    print("📋 Conectare la Google Sheets...")
    try:
        sheets_manager = GoogleSheetsManager(
            config.GOOGLE_SHEETS_CREDENTIALS_PATH,
            config.GOOGLE_SHEETS_SPREADSHEET_ID
        )
        print("✅ Conectat cu succes")
    except Exception as e:
        print(f"❌ Eroare: {e}")
        return False
    print()
    
    # Obține cărți
    print("📚 Obținere cărți din Crime Fiction - US...")
    try:
        books = sheets_manager.get_all_books('Crime Fiction - US')
        if not books:
            print("❌ Nu s-au găsit cărți")
            return False
        print(f"✅ Găsite {len(books)} cărți")
    except Exception as e:
        print(f"❌ Eroare: {e}")
        return False
    print()
    
    # Test pe primele 3 cărți
    test_books = books[:3]
    print(f"🖼️  Test extragere imagini pentru {len(test_books)} cărți...")
    print()
    
    scraper = AmazonScraper(
        delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
        retry_attempts=config.AMAZON_RETRY_ATTEMPTS
    )
    
    results = []
    
    for i, book in enumerate(test_books, 1):
        print(f"📖 Carte {i}/{len(test_books)}: {book['name']}")
        print(f"   Autor: {book['author']}")
        print(f"   URL: {book['amazon_link']}")
        
        # Test 1: Metoda simplă (requests)
        print("   🔍 Test 1: Extragere cu requests...")
        try:
            cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=False)
            if cover_url:
                print(f"   ✅ Cover găsit: {cover_url[:80]}...")
                results.append({
                    'book': book['name'],
                    'method': 'requests',
                    'success': True,
                    'url': cover_url
                })
            else:
                print("   ⚠️  Cover nu a fost găsit cu requests")
                # Test 2: Metoda Playwright (fallback)
                print("   🔍 Test 2: Extragere cu Playwright (fallback)...")
                try:
                    cover_url = scraper.extract_cover_image(book['amazon_link'], use_playwright=True)
                    if cover_url:
                        print(f"   ✅ Cover găsit cu Playwright: {cover_url[:80]}...")
                        results.append({
                            'book': book['name'],
                            'method': 'playwright',
                            'success': True,
                            'url': cover_url
                        })
                    else:
                        print("   ❌ Cover nu a fost găsit nici cu Playwright")
                        results.append({
                            'book': book['name'],
                            'method': 'both',
                            'success': False,
                            'url': None
                        })
                except Exception as e:
                    print(f"   ❌ Eroare Playwright: {e}")
                    results.append({
                        'book': book['name'],
                        'method': 'playwright',
                        'success': False,
                        'error': str(e)
                    })
        except Exception as e:
            print(f"   ❌ Eroare requests: {e}")
            results.append({
                'book': book['name'],
                'method': 'requests',
                'success': False,
                'error': str(e)
            })
        
        print()
    
    # Rezumat
    print("=" * 60)
    print("📊 REZUMAT")
    print("=" * 60)
    success_count = sum(1 for r in results if r.get('success'))
    print(f"✅ Succese: {success_count}/{len(results)}")
    print(f"❌ Eșecuri: {len(results) - success_count}/{len(results)}")
    print()
    
    if success_count > 0:
        print("📸 Imagini extrase cu succes:")
        for r in results:
            if r.get('success'):
                print(f"   ✅ {r['book']} ({r['method']})")
                print(f"      {r['url'][:100]}...")
    print()
    
    return success_count > 0

if __name__ == '__main__':
    success = test_extract_cover_images()
    sys.exit(0 if success else 1)
