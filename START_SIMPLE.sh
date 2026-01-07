#!/bin/bash
# Script simplu pentru pornirea tuturor serviciilor

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 Pornire Microservicii..."
echo ""

# Verifică Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis nu rulează. Pornire Redis..."
    brew services start redis 2>/dev/null || redis-server &
    sleep 2
fi

# Oprește servicii existente
lsof -ti:8001,8002,5001 2>/dev/null | xargs kill 2>/dev/null || true
sleep 1

# Pornește Sheets Service
echo "📊 Pornire Sheets Service (port 8001)..."
cd services/sheets-service
python3 main.py > ../../logs/sheets-service.log 2>&1 &
SHEETS_PID=$!
cd ../..
sleep 2

# Pornește Scraper Service
echo "🕷️  Pornire Scraper Service (port 8002)..."
cd services/scraper-service
python3 main.py > ../../logs/scraper-service.log 2>&1 &
SCRAPER_PID=$!
cd ../..
sleep 2

# Pornește API Service
echo "🌐 Pornire API Service (port 5001)..."
cd services/api-service
python3 main.py > ../../logs/api-service.log 2>&1 &
API_PID=$!
cd ../..
sleep 2

# Pornește Worker Service
echo "⚙️  Pornire Worker Service..."
cd services/worker-service
celery -A celery_app worker --loglevel=info > ../../logs/worker-service.log 2>&1 &
WORKER_PID=$!
cd ../..
sleep 2

echo ""
echo "✅ Toate serviciile pornite!"
echo ""
echo "📊 Status:"
echo "  - Sheets Service:  http://localhost:8001 (PID: $SHEETS_PID)"
echo "  - Scraper Service: http://localhost:8002 (PID: $SCRAPER_PID)"
echo "  - API Service:     http://localhost:5001 (PID: $API_PID)"
echo "  - Worker Service:  PID $WORKER_PID"
echo ""
echo "🌐 Dashboard: http://localhost:5001/"
echo ""
echo "📝 Logs:"
echo "  tail -f logs/sheets-service.log"
echo "  tail -f logs/scraper-service.log"
echo "  tail -f logs/api-service.log"
echo "  tail -f logs/worker-service.log"
echo ""
echo "🛑 Pentru oprire:"
echo "  lsof -ti:8001,8002,5001 | xargs kill"
echo "  pkill -f 'celery.*celery_app'"
echo ""

# Salvează PIDs
echo "$SHEETS_PID $SCRAPER_PID $API_PID $WORKER_PID" > .service_pids

