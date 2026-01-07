#!/bin/bash
# Script pentru pornirea tuturor microserviciilor

set -e

echo "🚀 Starting all microservices..."

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis nu rulează!"
    echo "📦 Pornire Redis..."
    brew services start redis 2>/dev/null || redis-server &
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis pornit cu succes!"
    else
        echo "❌ Eroare la pornirea Redis. Verifică manual: redis-cli ping"
        exit 1
    fi
else
    echo "✅ Redis rulează deja"
fi

echo ""

# Start sheets-service
echo "📊 Starting sheets-service..."
cd services/sheets-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001 > ../../logs/sheets-service.log 2>&1 &
SHEETS_PID=$!
echo "✅ sheets-service started (PID: $SHEETS_PID)"
cd ../..

sleep 2

# Start scraper-service
echo "🕷️  Starting scraper-service..."
cd services/scraper-service
python -m uvicorn main:app --host 0.0.0.0 --port 8002 > ../../logs/scraper-service.log 2>&1 &
SCRAPER_PID=$!
echo "✅ scraper-service started (PID: $SCRAPER_PID)"
cd ../..

sleep 2

# Start api-service
echo "🌐 Starting api-service..."
cd services/api-service
python -m uvicorn main:app --host 0.0.0.0 --port 5001 > ../../logs/api-service.log 2>&1 &
API_PID=$!
echo "✅ api-service started (PID: $API_PID)"
cd ../..

sleep 2

# Start worker-service
echo "⚙️  Starting worker-service..."
cd services/worker-service
celery -A celery_app worker --loglevel=info > ../../logs/worker-service.log 2>&1 &
WORKER_PID=$!
echo "✅ worker-service started (PID: $WORKER_PID)"
cd ../..

echo ""
echo "✅ All services started!"
echo ""
echo "📋 Service URLs:"
echo "   - sheets-service:  http://localhost:8001"
echo "   - scraper-service: http://localhost:8002"
echo "   - api-service:     http://localhost:5001"
echo ""
echo "📝 Logs:"
echo "   - sheets-service:  logs/sheets-service.log"
echo "   - scraper-service: logs/scraper-service.log"
echo "   - api-service:     logs/api-service.log"
echo "   - worker-service:  logs/worker-service.log"
echo ""
echo "🛑 To stop all services:"
echo "   kill $SHEETS_PID $SCRAPER_PID $API_PID $WORKER_PID"

# Save PIDs to file
echo "$SHEETS_PID $SCRAPER_PID $API_PID $WORKER_PID" > .service_pids

