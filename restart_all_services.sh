#!/bin/bash
# Script pentru restart complet al tuturor serviciilor
# Rulează scraping-ul zilnic la 10:00 AM (ora României)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔄 Restart complet al tuturor serviciilor..."
echo ""

# Verifică dacă există venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment nu există! Rulează: python3 -m venv venv"
    exit 1
fi

# Activează venv
source venv/bin/activate

# Oprește toate procesele existente
echo "🛑 Oprire servicii existente..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
pkill -f "python.*scheduler.py" 2>/dev/null || true
pkill -f "redis-server" 2>/dev/null || true
sleep 2

# Verifică și pornește Redis
echo "🔴 Verificare Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "   Pornire Redis..."
    if command -v redis-server > /dev/null; then
        redis-server --daemonize yes 2>/dev/null || redis-server &
        sleep 2
        if redis-cli ping > /dev/null 2>&1; then
            echo "   ✅ Redis pornit"
        else
            echo "   ⚠️  Redis nu pornește automat. Pornește-l manual: redis-server"
        fi
    else
        echo "   ⚠️  Redis nu este instalat. Instalează-l: brew install redis (Mac) sau apt-get install redis (Linux)"
    fi
else
    echo "   ✅ Redis rulează deja"
fi

# Șterge cache Python
echo "🧹 Curățare cache Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Creează directorul pentru logs dacă nu există
mkdir -p logs

# Pornește Celery Worker (dacă este necesar)
echo "⚙️  Pornire Celery Worker..."
if [ -f "app/tasks/bsr_tasks.py" ] || [ -f "services/worker-service/celery_app.py" ]; then
    celery -A app.tasks.bsr_tasks worker --loglevel=info --detach --logfile=logs/celery-worker.log 2>/dev/null || \
    celery -A services.worker-service.celery_app worker --loglevel=info --detach --logfile=logs/celery-worker.log 2>/dev/null || \
    echo "   ⚠️  Celery worker nu pornește (poate nu este configurat)"
    sleep 2
fi

# Pornește FastAPI/uvicorn
echo "🌐 Pornire FastAPI Server..."
if [ -f "app/main.py" ]; then
    nohup uvicorn app.main:app --host 0.0.0.0 --port 5001 > logs/fastapi.log 2>&1 &
    FASTAPI_PID=$!
    echo "   ✅ FastAPI pornit (PID: $FASTAPI_PID)"
    sleep 3
else
    echo "   ⚠️  app/main.py nu există"
fi

# Verifică statusul serviciilor
echo ""
echo "📊 Status servicii:"
echo ""

# Verifică Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis: RUNNING"
else
    echo "   ❌ Redis: STOPPED"
fi

# Verifică Celery
if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ✅ Celery Worker: RUNNING"
else
    echo "   ⚠️  Celery Worker: NOT RUNNING (poate nu este necesar)"
fi

# Verifică FastAPI
if pgrep -f "uvicorn.*app.main:app" > /dev/null; then
    echo "   ✅ FastAPI: RUNNING"
    echo "   🌐 URL: http://localhost:5001"
else
    echo "   ❌ FastAPI: STOPPED"
fi

echo ""
echo "✅ Restart complet!"
echo ""
echo "📝 Logs disponibile în:"
echo "   - logs/fastapi.log"
echo "   - logs/celery-worker.log"
echo ""
echo "🕐 Scheduler configurat pentru: 10:00 AM (ora României - Europe/Bucharest)"
echo ""
echo "🔍 Verificare status:"
echo "   tail -f logs/fastapi.log"
echo "   curl http://localhost:5001/api/scheduler-status"
echo ""

