#!/usr/bin/env python3
"""
Test final - verificare job status și alte endpoint-uri
"""
import requests
import json
import time

BASE_URL = "http://localhost:5001"

print("🔍 TESTE SUPLIMENTARE")
print("=" * 50)
print()

# Test 1: Job status (dacă există un job)
print("📋 TEST 1: Job status")
print("-" * 50)
# Folosim job_id din testul anterior sau testăm cu unul nou
try:
    # Trigger un job nou
    response = requests.post(f"{BASE_URL}/api/trigger-bsr-update", 
                           json={"worksheet": "Crime Fiction - US"},
                           timeout=5)
    if response.status_code == 200:
        data = response.json()
        job_id = data.get("job_id")
        if job_id:
            print(f"   ✅ Job creat: {job_id}")
            time.sleep(1)
            # Verifică status
            status_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}", timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   📊 Status job: {status_data.get('state', 'N/A')}")
                print(f"   📝 Message: {status_data.get('status', 'N/A')}")
                if 'progress' in status_data:
                    progress = status_data['progress']
                    print(f"   📈 Progress: {progress.get('current', 0)}/{progress.get('total', 0)}")
            else:
                print(f"   ⚠️  Nu s-a putut obține status (cod: {status_response.status_code})")
        else:
            print(f"   ⚠️  Job executat direct (fără Redis/Celery)")
    else:
        print(f"   ❌ Eroare la crearea job-ului: {response.status_code}")
except Exception as e:
    print(f"   ⚠️  Eroare: {e}")
print()

# Test 2: Verificare ETag și caching
print("📋 TEST 2: Verificare ETag și caching")
print("-" * 50)
try:
    # Prima cerere
    response1 = requests.get(f"{BASE_URL}/api/rankings?worksheet=Crime%20Fiction%20-%20US", timeout=10)
    etag1 = response1.headers.get("ETag")
    last_modified1 = response1.headers.get("Last-Modified")
    
    print(f"   ✅ Prima cerere: Status {response1.status_code}")
    if etag1:
        print(f"   🏷️  ETag: {etag1[:50]}...")
    if last_modified1:
        print(f"   📅 Last-Modified: {last_modified1}")
    
    # A doua cerere cu If-None-Match
    if etag1:
        headers = {"If-None-Match": etag1}
        response2 = requests.get(f"{BASE_URL}/api/rankings?worksheet=Crime%20Fiction%20-%20US", 
                                headers=headers, timeout=10)
        print(f"   ✅ Cerere cu If-None-Match: Status {response2.status_code}")
        if response2.status_code == 304:
            print(f"   ✅ Cache funcționează corect (304 Not Modified)")
except Exception as e:
    print(f"   ⚠️  Eroare: {e}")
print()

# Test 3: Test pentru toate sheet-urile - chart data
print("📋 TEST 3: Chart data pentru toate sheet-urile")
print("-" * 50)
worksheets = ["Crime Fiction - US", "Crime Fiction - UK"]
for ws in worksheets:
    encoded = ws.replace(" ", "%20")
    try:
        response = requests.get(f"{BASE_URL}/api/chart-data?range=30&worksheet={encoded}", timeout=10)
        if response.status_code == 200:
            data = response.json()
            dates = len(data.get("dates", []))
            books = data.get("total_books", 0)
            print(f"   ✅ {ws}: {dates} date, {books} cărți")
        else:
            print(f"   ❌ {ws}: Status {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  {ws}: Eroare {e}")
print()

# Test 4: Verificare structură date pentru o carte
print("📋 TEST 4: Structură date pentru o carte")
print("-" * 50)
try:
    response = requests.get(f"{BASE_URL}/api/books?worksheet=Crime%20Fiction%20-%20US", timeout=10)
    if response.status_code == 200:
        books = response.json()
        if books:
            book = books[0]
            print(f"   📖 Carte: {book.get('name', 'N/A')}")
            print(f"   👤 Autor: {book.get('author', 'N/A')}")
            print(f"   🔗 Link: {book.get('amazon_link', 'N/A')[:50]}...")
            print(f"   📊 BSR curent: {book.get('current_bsr', 'N/A')}")
            print(f"   📈 Istoric: {len(book.get('bsr_history', []))} intrări")
            print(f"   🖼️  Cover: {'Da' if book.get('cover_image') else 'Nu'}")
            if book.get('bsr_history'):
                first_entry = book['bsr_history'][0]
                print(f"   📅 Prima intrare: {first_entry.get('date')} - BSR: {first_entry.get('bsr')}")
except Exception as e:
    print(f"   ⚠️  Eroare: {e}")
print()

# Test 5: Verificare performanță
print("📋 TEST 5: Verificare performanță")
print("-" * 50)
import time
endpoints = [
    ("/api/worksheets", "GET"),
    ("/api/books?worksheet=Crime%20Fiction%20-%20US", "GET"),
    ("/api/rankings?worksheet=Crime%20Fiction%20-%20US", "GET"),
    ("/api/chart-data?range=30&worksheet=Crime%20Fiction%20-%20US", "GET"),
]

for endpoint, method in endpoints:
    try:
        start = time.time()
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=15)
        elapsed = time.time() - start
        status = "✅" if response.status_code == 200 else "❌"
        print(f"   {status} {endpoint[:40]:<40} {elapsed:.3f}s")
    except Exception as e:
        print(f"   ❌ {endpoint[:40]:<40} Eroare: {e}")
print()

print("=" * 50)
print("✅ TOATE TESTELE FINALIZATE!")
print("=" * 50)
