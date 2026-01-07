#!/bin/bash

echo "🧪 TESTARE COMPLETĂ API - PAS CU PAS"
echo "======================================"
echo ""

BASE_URL="http://localhost:5001"

# Test 1: Health check / Root
echo "📋 TEST 1: Root endpoint"
echo "------------------------"
curl -s "$BASE_URL/" | head -5
echo ""
echo ""

# Test 2: Lista worksheets
echo "📋 TEST 2: Lista toate worksheet-urile"
echo "--------------------------------------"
curl -s "$BASE_URL/api/worksheets" | python3 -m json.tool
echo ""
echo ""

# Test 3: Cărți pentru fiecare worksheet
echo "📋 TEST 3: Cărți pentru fiecare worksheet"
echo "------------------------------------------"
for sheet in "Sheet1" "Crime Fiction - US" "Crime Fiction - UK" "Sheet3"; do
    encoded=$(echo "$sheet" | sed 's/ /%20/g')
    echo "  📚 $sheet:"
    curl -s "$BASE_URL/api/books?worksheet=$encoded" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'    ✅ {len(data)} cărți')" 2>/dev/null || echo "    ❌ Eroare"
done
echo ""

# Test 4: Rankings pentru fiecare worksheet
echo "📋 TEST 4: Rankings pentru fiecare worksheet"
echo "--------------------------------------------"
for sheet in "Sheet1" "Crime Fiction - US" "Crime Fiction - UK"; do
    encoded=$(echo "$sheet" | sed 's/ /%20/g')
    echo "  🏆 $sheet:"
    curl -s "$BASE_URL/api/rankings?worksheet=$encoded" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'    ✅ {len(data)} cărți cu ranking')" 2>/dev/null || echo "    ❌ Eroare"
done
echo ""

# Test 5: Chart data pentru diferite range-uri
echo "📋 TEST 5: Chart data pentru diferite range-uri"
echo "-----------------------------------------------"
for range in "1" "7" "30" "90" "365" "all"; do
    echo "  📊 Range: $range zile"
    curl -s "$BASE_URL/api/chart-data?range=$range&worksheet=Crime%20Fiction%20-%20US" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'    ✅ {len(data.get(\"dates\", []))} date, {data.get(\"total_books\", 0)} cărți')" 2>/dev/null || echo "    ❌ Eroare"
done
echo ""

# Test 6: Scheduler status
echo "📋 TEST 6: Scheduler status"
echo "---------------------------"
curl -s "$BASE_URL/api/scheduler-status" | python3 -m json.tool
echo ""
echo ""

# Test 7: Clear cache
echo "📋 TEST 7: Clear cache"
echo "---------------------"
curl -s -X GET "$BASE_URL/api/clear-cache" | python3 -m json.tool
echo ""
echo ""

# Test 8: Detalii cărți (prima carte din Crime Fiction - US)
echo "📋 TEST 8: Detalii prima carte (Crime Fiction - US)"
echo "----------------------------------------------------"
curl -s "$BASE_URL/api/books?worksheet=Crime%20Fiction%20-%20US" | python3 -c "import sys, json; data=json.load(sys.stdin); book=data[0] if data else {}; print(f'  Nume: {book.get(\"name\", \"N/A\")}'); print(f'  Autor: {book.get(\"author\", \"N/A\")}'); print(f'  BSR curent: {book.get(\"current_bsr\", \"N/A\")}'); print(f'  Istoric: {len(book.get(\"bsr_history\", []))} intrări')" 2>/dev/null
echo ""
echo ""

echo "✅ TESTARE COMPLETĂ FINALIZATĂ!"
