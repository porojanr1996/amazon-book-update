#!/usr/bin/env python3
"""
Test detaliat pentru toate endpoint-urile API
"""
import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:5001"

def test_endpoint(name: str, method: str, url: str, **kwargs) -> Dict[str, Any]:
    """Testează un endpoint și returnează rezultatul"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10, **kwargs)
        elif method.upper() == "POST":
            response = requests.post(url, timeout=10, **kwargs)
        else:
            return {"status": "error", "message": f"Method {method} not supported"}
        
        result = {
            "status": "success" if response.status_code == 200 else "error",
            "status_code": response.status_code,
            "url": url
        }
        
        try:
            result["data"] = response.json()
        except:
            result["data"] = response.text[:200]
        
        return result
    except Exception as e:
        return {"status": "error", "message": str(e), "url": url}

def print_test(name: str, result: Dict[str, Any]):
    """Afișează rezultatul unui test"""
    status_icon = "✅" if result["status"] == "success" else "❌"
    print(f"{status_icon} {name}")
    print(f"   Status: {result.get('status_code', 'N/A')}")
    if result["status"] == "error":
        print(f"   Eroare: {result.get('message', 'Unknown')}")
    elif isinstance(result.get("data"), dict):
        # Afișează informații relevante
        data = result["data"]
        if "worksheets" in str(data) or isinstance(data, list):
            print(f"   Rezultat: {len(data) if isinstance(data, list) else 'N/A'} iteme")
        elif "total_books" in data:
            print(f"   Rezultat: {data.get('total_books')} cărți, {len(data.get('dates', []))} date")
        else:
            print(f"   Rezultat: {type(data).__name__}")
    print()

print("🧪 TESTARE DETALIATĂ API - PAS CU PAS")
print("=" * 50)
print()

# Test 1: Worksheets
print("📋 TEST 1: Lista worksheets")
print("-" * 50)
result = test_endpoint("GET /api/worksheets", "GET", f"{BASE_URL}/api/worksheets")
print_test("GET /api/worksheets", result)
if result["status"] == "success":
    worksheets = result["data"]
    print(f"   📊 Worksheet-uri găsite: {len(worksheets)}")
    for ws in worksheets:
        print(f"      - {ws}")
    print()

# Test 2: Books pentru fiecare worksheet
print("📋 TEST 2: Books pentru fiecare worksheet")
print("-" * 50)
for worksheet in worksheets:
    encoded = worksheet.replace(" ", "%20")
    result = test_endpoint(f"GET /api/books?worksheet={worksheet}", "GET", 
                          f"{BASE_URL}/api/books?worksheet={encoded}")
    print_test(f"Books pentru '{worksheet}'", result)
    if result["status"] == "success":
        books = result["data"]
        print(f"      📚 {len(books)} cărți găsite")
        if books:
            first_book = books[0]
            print(f"      📖 Exemplu: {first_book.get('name', 'N/A')} - {first_book.get('author', 'N/A')}")
    print()

# Test 3: Rankings pentru fiecare worksheet
print("📋 TEST 3: Rankings pentru fiecare worksheet")
print("-" * 50)
for worksheet in worksheets[:3]:  # Test doar primele 3
    encoded = worksheet.replace(" ", "%20")
    result = test_endpoint(f"GET /api/rankings?worksheet={worksheet}", "GET",
                          f"{BASE_URL}/api/rankings?worksheet={encoded}")
    print_test(f"Rankings pentru '{worksheet}'", result)
    if result["status"] == "success":
        rankings = result["data"]
        print(f"      🏆 {len(rankings)} cărți cu ranking")
        if rankings:
            # Primele 3 cărți sortate
            print(f"      Top 3:")
            for i, book in enumerate(rankings[:3], 1):
                bsr = book.get('current_bsr', 'N/A')
                print(f"         {i}. {book.get('name', 'N/A')} - BSR: {bsr}")
    print()

# Test 4: Chart data pentru diferite range-uri
print("📋 TEST 4: Chart data pentru diferite range-uri")
print("-" * 50)
test_worksheet = "Crime Fiction - US"
for range_val in ["1", "7", "30", "90", "365", "all"]:
    encoded = test_worksheet.replace(" ", "%20")
    result = test_endpoint(f"GET /api/chart-data?range={range_val}", "GET",
                          f"{BASE_URL}/api/chart-data?range={range_val}&worksheet={encoded}")
    print_test(f"Chart data (range={range_val})", result)
    if result["status"] == "success":
        chart_data = result["data"]
        dates_count = len(chart_data.get("dates", []))
        books_count = chart_data.get("total_books", 0)
        print(f"      📊 {dates_count} date, {books_count} cărți")
    print()

# Test 5: Scheduler status
print("📋 TEST 5: Scheduler status")
print("-" * 50)
result = test_endpoint("GET /api/scheduler-status", "GET", f"{BASE_URL}/api/scheduler-status")
print_test("Scheduler status", result)
if result["status"] == "success":
    scheduler = result["data"]
    print(f"      ⏰ Running: {scheduler.get('running', False)}")
    if scheduler.get("next_run"):
        print(f"      📅 Next run: {scheduler.get('next_run')}")
    print(f"      📋 Jobs: {len(scheduler.get('jobs', []))}")
print()

# Test 6: Clear cache
print("📋 TEST 6: Clear cache")
print("-" * 50)
result = test_endpoint("GET /api/clear-cache", "GET", f"{BASE_URL}/api/clear-cache")
print_test("Clear cache", result)
if result["status"] == "success":
    print(f"      🗑️  {result['data'].get('message', 'N/A')}")
print()

# Test 7: Trigger BSR update (doar verificare, nu executăm efectiv)
print("📋 TEST 7: Trigger BSR update endpoint (verificare)")
print("-" * 50)
result = test_endpoint("POST /api/trigger-bsr-update", "POST", 
                      f"{BASE_URL}/api/trigger-bsr-update",
                      json={"worksheet": "Crime Fiction - US"})
print_test("Trigger BSR update", result)
if result["status"] == "success":
    data = result["data"]
    print(f"      🔄 Status: {data.get('status', 'N/A')}")
    print(f"      📝 Message: {data.get('message', 'N/A')}")
    if "job_id" in data:
        print(f"      🆔 Job ID: {data.get('job_id', 'N/A')}")
print()

print("=" * 50)
print("✅ TESTARE COMPLETĂ FINALIZATĂ!")
print("=" * 50)
