#!/usr/bin/env python3
"""
Test script pentru verificarea extragerii corecte a BSR-ului principal
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from amazon_scraper import AmazonScraper
import config

print("🧪 TEST EXTRAGERE BSR PRINCIPAL")
print("=" * 60)
print()

# Test cu un URL real (înlocuiește cu un URL real din Google Sheets)
test_url = input("Introdu URL-ul unei cărți de test (sau apasă Enter pentru skip): ").strip()

if not test_url:
    print("⚠️  Skip test - nu ai introdus URL")
    sys.exit(0)

print()
print(f"🔍 Testare extragere BSR pentru: {test_url}")
print("-" * 60)

scraper = AmazonScraper(
    delay_between_requests=config.AMAZON_DELAY_BETWEEN_REQUESTS,
    retry_attempts=1  # Doar 1 încercare pentru test
)

# Test 1: Extragere cu requests (folosește parser strict)
print("\n1️⃣  Test cu requests (parser strict):")
bsr1 = scraper.extract_bsr(test_url, use_playwright=False)
if bsr1:
    print(f"   ✅ BSR extras: #{bsr1:,}")
    if bsr1 < 100:
        print(f"   ⚠️  ATENȚIE: BSR foarte mic ({bsr1}) - ar putea fi ranking de categorie!")
    elif bsr1 < 1000:
        print(f"   ⚠️  BSR mic ({bsr1}) - verifică dacă este corect")
    else:
        print(f"   ✅ BSR pare rezonabil (>= 1000)")
else:
    print(f"   ❌ Nu s-a putut extrage BSR")

# Test 2: Extragere cu Playwright (dacă e necesar)
print("\n2️⃣  Test cu Playwright (parser strict):")
bsr2 = scraper.extract_bsr(test_url, use_playwright=True)
if bsr2:
    print(f"   ✅ BSR extras: #{bsr2:,}")
    if bsr2 < 100:
        print(f"   ⚠️  ATENȚIE: BSR foarte mic ({bsr2}) - ar putea fi ranking de categorie!")
    elif bsr2 < 1000:
        print(f"   ⚠️  BSR mic ({bsr2}) - verifică dacă este corect")
    else:
        print(f"   ✅ BSR pare rezonabil (>= 1000)")
else:
    print(f"   ❌ Nu s-a putut extrage BSR")

print()
print("=" * 60)
print("📊 REZUMAT:")
print(f"   Requests: {'✅' if bsr1 else '❌'} {bsr1 if bsr1 else 'N/A'}")
print(f"   Playwright: {'✅' if bsr2 else '❌'} {bsr2 if bsr2 else 'N/A'}")

if bsr1 and bsr2 and bsr1 != bsr2:
    print(f"   ⚠️  Diferență între metode: {bsr1} vs {bsr2}")
elif bsr1 or bsr2:
    print(f"   ✅ BSR extras cu succes!")
else:
    print(f"   ❌ Nu s-a putut extrage BSR cu niciuna dintre metode")

print()
print("💡 Verifică manual pe Amazon că BSR-ul extras este corect!")
print("   BSR-ul principal ar trebui să fie cel cu 'in Kindle Store'")
print("   Nu ranking-urile de categorii (ex: '6 in Scandinavian Crime')")

