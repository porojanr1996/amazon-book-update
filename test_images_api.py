#!/usr/bin/env python3
"""
Test extragere imagini prin API
"""
import requests
import json
import time

BASE_URL = "http://localhost:5001"

print("🖼️  TEST EXTRAGERE IMAGINI PRIN API")
print("=" * 50)
print()

# Test 1: Obține rankings (care ar trebui să extragă imagini)
print("📋 TEST 1: Rankings cu extragere imagini")
print("-" * 50)
print("   ⏳ Se extrag imagini pentru primele cărți (poate dura câteva secunde)...")
print()

start_time = time.time()
response = requests.get(
    f"{BASE_URL}/api/rankings?worksheet=Crime%20Fiction%20-%20US",
    timeout=60
)
elapsed = time.time() - start_time

if response.status_code == 200:
    books = response.json()
    print(f"   ✅ Status: {response.status_code}")
    print(f"   ⏱️  Timp: {elapsed:.2f}s")
    print(f"   📚 Cărți: {len(books)}")
    print()
    
    # Verifică câte cărți au imagini
    books_with_images = [b for b in books if b.get('cover_image')]
    print(f"   🖼️  Cărți cu imagini: {len(books_with_images)}/{len(books)}")
    print()
    
    if books_with_images:
        print("   📸 Primele 5 cărți cu imagini:")
        for i, book in enumerate(books_with_images[:5], 1):
            cover = book.get('cover_image', 'N/A')
            print(f"      {i}. {book.get('name', 'N/A')}")
            print(f"         🖼️  {cover[:80]}..." if cover and cover != 'N/A' else "         ❌ Fără imagine")
    else:
        print("   ⚠️  Niciun cover image extras (poate fi în cache sau nu s-au extras)")
else:
    print(f"   ❌ Eroare: Status {response.status_code}")
    print(f"   {response.text[:200]}")

print()
print("=" * 50)
print("✅ TEST FINALIZAT!")
print("=" * 50)
