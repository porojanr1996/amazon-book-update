#!/usr/bin/env python3
"""
Test script pentru verificarea extragerii BSR pentru URL-uri Amazon UK
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from amazon_scraper import AmazonScraper
import config

# URL-uri de test
test_urls = [
    "https://www.amazon.co.uk/gp/product/B0DXN9WZGG?ref",
    "https://www.amazon.co.uk/gp/product/B08KPJVQN3?ref",
    "https://www.amazon.co.uk/gp/product/B0CJRR38LP?ref",
    "https://www.amazon.co.uk/gp/product/B096MN4WRX?ref",
]

print("🧪 TEST EXTRAGERE BSR PENTRU AMAZON UK")
print("=" * 60)
print()

scraper = AmazonScraper(
    delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
    retry_attempts=1  # Doar 1 încercare pentru test rapid
)

results = []

for i, url in enumerate(test_urls, 1):
    print(f"\n📚 [{i}/{len(test_urls)}] Testare: {url}")
    print("-" * 60)
    
    # Test 1: Requests (parser strict)
    print("1️⃣  Test cu requests (parser strict):")
    bsr1 = scraper.extract_bsr(url, use_playwright=False)
    if bsr1:
        print(f"   ✅ BSR extras: #{bsr1:,}")
        if bsr1 < 100:
            print(f"   ⚠️  ATENȚIE: BSR foarte mic ({bsr1}) - posibil ranking de categorie!")
        elif bsr1 < 1000:
            print(f"   ⚠️  BSR mic ({bsr1}) - verifică manual")
        else:
            print(f"   ✅ BSR pare rezonabil")
    else:
        print(f"   ❌ Nu s-a putut extrage BSR cu requests")
    
    # Test 2: Playwright (parser strict)
    print("\n2️⃣  Test cu Playwright (parser strict):")
    try:
        bsr2 = scraper.extract_bsr(url, use_playwright=True)
        if bsr2:
            print(f"   ✅ BSR extras: #{bsr2:,}")
            if bsr2 < 100:
                print(f"   ⚠️  ATENȚIE: BSR foarte mic ({bsr2}) - posibil ranking de categorie!")
            elif bsr2 < 1000:
                print(f"   ⚠️  BSR mic ({bsr2}) - verifică manual")
            else:
                print(f"   ✅ BSR pare rezonabil")
        else:
            print(f"   ❌ Nu s-a putut extrage BSR cu Playwright")
    except Exception as e:
        print(f"   ❌ Eroare Playwright: {e}")
        bsr2 = None
    
    results.append({
        'url': url,
        'bsr_requests': bsr1,
        'bsr_playwright': bsr2
    })
    
    print()

print("=" * 60)
print("📊 REZUMAT:")
print("=" * 60)

for i, result in enumerate(results, 1):
    print(f"\n{i}. {result['url']}")
    print(f"   Requests: {'✅' if result['bsr_requests'] else '❌'} {result['bsr_requests'] if result['bsr_requests'] else 'N/A'}")
    print(f"   Playwright: {'✅' if result['bsr_playwright'] else '❌'} {result['bsr_playwright'] if result['bsr_playwright'] else 'N/A'}")
    
    if result['bsr_requests'] and result['bsr_playwright']:
        if result['bsr_requests'] != result['bsr_playwright']:
            print(f"   ⚠️  Diferență: {result['bsr_requests']} vs {result['bsr_playwright']}")

print("\n💡 Dacă ambele metode eșuează, Amazon UK poate bloca accesul.")
print("   Verifică manual pe Amazon că BSR-ul există pe pagină.")

