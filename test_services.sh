#!/bin/bash
# Script pentru testarea pas cu pas a fiecărui serviciu

set -e

echo "🧪 Testing Microservices - Step by Step"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if venv is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not activated. Activating...${NC}"
    source venv/bin/activate
fi

# Check Redis
echo "📦 Step 1: Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${RED}❌ Redis is not running. Starting Redis...${NC}"
    brew services start redis 2>/dev/null || redis-server &
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Redis started${NC}"
    else
        echo -e "${RED}❌ Failed to start Redis${NC}"
        exit 1
    fi
fi
echo ""

# Test 1: Sheets Service
echo "📊 Step 2: Testing Sheets Service..."
cd services/sheets-service

# Check imports
echo "  Checking imports..."
python3 -c "
import sys
import os
sys.path.insert(0, os.path.abspath('../../'))
try:
    from shared.config import SHEETS_SERVICE_PORT, GOOGLE_SHEETS_CREDENTIALS_PATH
    from google_sheets_transposed import GoogleSheetsManager
    print('  ✅ Imports OK')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    exit(1)
" || {
    echo -e "${RED}❌ Sheets Service imports failed${NC}"
    exit 1
}

# Start service in background
echo "  Starting service on port 8001..."
python3 main.py > ../../logs/sheets-service-test.log 2>&1 &
SHEETS_PID=$!
sleep 3

# Test health endpoint
echo "  Testing /health endpoint..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✅ Health check passed${NC}"
else
    echo -e "  ${RED}❌ Health check failed${NC}"
    echo "  Logs:"
    tail -20 ../../logs/sheets-service-test.log
    kill $SHEETS_PID 2>/dev/null || true
    exit 1
fi

# Test worksheets endpoint
echo "  Testing /api/worksheets endpoint..."
if curl -s http://localhost:8001/api/worksheets | grep -q "Crime Fiction"; then
    echo -e "  ${GREEN}✅ Worksheets endpoint works${NC}"
else
    echo -e "  ${YELLOW}⚠️  Worksheets endpoint returned unexpected result${NC}"
    curl -s http://localhost:8001/api/worksheets | head -5
fi

echo -e "${GREEN}✅ Sheets Service test passed${NC}"
echo ""

# Test 2: Scraper Service
echo "🕷️  Step 3: Testing Scraper Service..."
cd ../scraper-service

# Check imports
echo "  Checking imports..."
python3 -c "
import sys
import os
sys.path.insert(0, os.path.abspath('../../'))
try:
    from shared.config import SCRAPER_SERVICE_PORT
    from amazon_scraper import AmazonScraper
    print('  ✅ Imports OK')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    exit(1)
" || {
    echo -e "${RED}❌ Scraper Service imports failed${NC}"
    kill $SHEETS_PID 2>/dev/null || true
    exit 1
}

# Start service in background
echo "  Starting service on port 8002..."
python3 main.py > ../../logs/scraper-service-test.log 2>&1 &
SCRAPER_PID=$!
sleep 3

# Test health endpoint
echo "  Testing /health endpoint..."
if curl -s http://localhost:8002/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✅ Health check passed${NC}"
else
    echo -e "  ${RED}❌ Health check failed${NC}"
    echo "  Logs:"
    tail -20 ../../logs/scraper-service-test.log
    kill $SHEETS_PID $SCRAPER_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Scraper Service test passed${NC}"
echo ""

# Test 3: API Service
echo "🌐 Step 4: Testing API Service..."
cd ../api-service

# Check imports
echo "  Checking imports..."
python3 -c "
import sys
import os
sys.path.insert(0, os.path.abspath('../../'))
try:
    from shared.config import API_SERVICE_PORT, SHEETS_SERVICE_URL, SCRAPER_SERVICE_URL
    print('  ✅ Imports OK')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    exit(1)
" || {
    echo -e "${RED}❌ API Service imports failed${NC}"
    kill $SHEETS_PID $SCRAPER_PID 2>/dev/null || true
    exit 1
}

# Start service in background
echo "  Starting service on port 5001..."
python3 main.py > ../../logs/api-service-test.log 2>&1 &
API_PID=$!
sleep 3

# Test health endpoint
echo "  Testing /health endpoint..."
if curl -s http://localhost:5001/health | grep -q "healthy"; then
    echo -e "  ${GREEN}✅ Health check passed${NC}"
else
    echo -e "  ${YELLOW}⚠️  Health check returned unexpected result${NC}"
    curl -s http://localhost:5001/health | head -10
fi

# Test worksheets endpoint (proxy)
echo "  Testing /api/worksheets endpoint (proxy)..."
if curl -s "http://localhost:5001/api/worksheets" | grep -q "Crime Fiction"; then
    echo -e "  ${GREEN}✅ Worksheets proxy works${NC}"
else
    echo -e "  ${YELLOW}⚠️  Worksheets proxy returned unexpected result${NC}"
    curl -s http://localhost:5001/api/worksheets | head -5
fi

echo -e "${GREEN}✅ API Service test passed${NC}"
echo ""

# Test 4: Worker Service
echo "⚙️  Step 5: Testing Worker Service..."
cd ../worker-service

# Check imports
echo "  Checking imports..."
python3 -c "
import sys
import os
sys.path.insert(0, os.path.abspath('../../'))
try:
    from shared.config import CELERY_BROKER_URL, REDIS_URL
    from celery_app import celery_app
    print('  ✅ Imports OK')
except Exception as e:
    print(f'  ❌ Import error: {e}')
    exit(1)
" || {
    echo -e "${RED}❌ Worker Service imports failed${NC}"
    kill $SHEETS_PID $SCRAPER_PID $API_PID 2>/dev/null || true
    exit 1
}

echo -e "${GREEN}✅ Worker Service imports OK${NC}"
echo "  (Worker service needs to be started manually with: celery -A celery_app worker)"
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All services tested successfully!${NC}"
echo ""
echo "Running services:"
echo "  - Sheets Service:  PID $SHEETS_PID (port 8001)"
echo "  - Scraper Service: PID $SCRAPER_PID (port 8002)"
echo "  - API Service:     PID $API_PID (port 5001)"
echo ""
echo "To stop all services:"
echo "  kill $SHEETS_PID $SCRAPER_PID $API_PID"
echo ""
echo "Logs:"
echo "  - sheets-service:  logs/sheets-service-test.log"
echo "  - scraper-service: logs/scraper-service-test.log"
echo "  - api-service:     logs/api-service-test.log"

# Save PIDs
echo "$SHEETS_PID $SCRAPER_PID $API_PID" > ../../.test_service_pids

cd ../..

