#!/bin/bash

# Test script pentru aplicația locală
# Usage: ./test_local.sh

echo "🧪 Testing Amazon BSR Tracking System"
echo "========================================"
echo ""

BASE_URL="http://localhost:5001"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if server is running
echo "1️⃣  Testing server connection..."
if curl -s "$BASE_URL/" > /dev/null; then
    echo -e "${GREEN}✓${NC} Server is running on port 5001"
else
    echo -e "${RED}✗${NC} Server is not running. Start it with: python app.py"
    exit 1
fi
echo ""

# Test 2: Test categories endpoint
echo "2️⃣  Testing categories endpoint..."
CATEGORIES=$(curl -s "$BASE_URL/api/categories")
if [ "$CATEGORIES" != "" ]; then
    echo -e "${GREEN}✓${NC} Categories endpoint works"
    echo "   Categories found: $CATEGORIES"
else
    echo -e "${YELLOW}⚠${NC} No categories found (this is OK if no categories are set)"
fi
echo ""

# Test 3: Test books endpoint
echo "3️⃣  Testing books endpoint..."
BOOKS_COUNT=$(curl -s "$BASE_URL/api/books" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ "$BOOKS_COUNT" != "" ] && [ "$BOOKS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Books endpoint works"
    echo "   Found $BOOKS_COUNT books"
else
    echo -e "${RED}✗${NC} Books endpoint failed or no books found"
fi
echo ""

# Test 4: Test chart data endpoint
echo "4️⃣  Testing chart data endpoint..."
CHART_DATA=$(curl -s "$BASE_URL/api/chart-data?range=30")
DATES_COUNT=$(echo "$CHART_DATA" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('dates', [])))" 2>/dev/null)
if [ "$DATES_COUNT" != "" ] && [ "$DATES_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓${NC} Chart data endpoint works"
    echo "   Found $DATES_COUNT data points"
else
    echo -e "${YELLOW}⚠${NC} Chart data endpoint works but no data points found (might be OK)"
fi
echo ""

# Test 5: Test rankings endpoint
echo "5️⃣  Testing rankings endpoint..."
RANKINGS_COUNT=$(curl -s "$BASE_URL/api/rankings" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data))" 2>/dev/null)
if [ "$RANKINGS_COUNT" != "" ]; then
    echo -e "${GREEN}✓${NC} Rankings endpoint works"
    echo "   Found $RANKINGS_COUNT rankings"
else
    echo -e "${RED}✗${NC} Rankings endpoint failed"
fi
echo ""

# Test 6: Test scheduler status
echo "6️⃣  Testing scheduler status..."
SCHEDULER_STATUS=$(curl -s "$BASE_URL/api/scheduler-status" 2>/dev/null)
if [ "$SCHEDULER_STATUS" != "" ]; then
    echo -e "${GREEN}✓${NC} Scheduler status endpoint works"
    echo "$SCHEDULER_STATUS" | python3 -m json.tool 2>/dev/null | head -10
else
    echo -e "${YELLOW}⚠${NC} Scheduler status endpoint not available (might be OK)"
fi
echo ""

# Test 7: Test different time ranges
echo "7️⃣  Testing time range filters..."
for range in "1" "7" "30" "90" "365" "all"; do
    RESPONSE=$(curl -s "$BASE_URL/api/chart-data?range=$range")
    if [ "$RESPONSE" != "" ]; then
        echo -e "   ${GREEN}✓${NC} Range '$range' works"
    else
        echo -e "   ${RED}✗${NC} Range '$range' failed"
    fi
done
echo ""

# Summary
echo "========================================"
echo "✅ Testing complete!"
echo ""
echo "🌐 Open browser at: $BASE_URL"
echo "📊 Dashboard should show:"
echo "   - Chart with average BSR over time"
echo "   - Top 50 rankings"
echo "   - Category filters (if categories exist)"
echo "   - Time range filters"
echo ""

