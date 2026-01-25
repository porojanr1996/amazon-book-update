#!/bin/bash
# Script pentru configurare Celery Worker pe EC2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "⚙️  Configurare Celery Worker..."
echo ""

# Verifică dacă există venv
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment nu există!"
    exit 1
fi

source venv/bin/activate

# Verifică Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis nu rulează! Pornește-l mai întâi:"
    echo "   ./fix_redis_ec2.sh"
    exit 1
fi

echo "✅ Redis rulează"
echo ""

# Verifică dacă Celery este instalat
if ! python3 -c "import celery" 2>/dev/null; then
    echo "📦 Instalare Celery..."
    pip install celery redis
fi

# Creează directorul pentru logs
mkdir -p logs

# Oprește worker-ul existent
echo "🛑 Oprire Celery Worker existent..."
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

# Pornește Celery Worker
echo "🚀 Pornire Celery Worker..."

# Verifică dacă există app/tasks/bsr_tasks.py
if [ -f "app/tasks/bsr_tasks.py" ]; then
    CELERY_APP="app.tasks.bsr_tasks"
elif [ -f "app/celery_app.py" ]; then
    CELERY_APP="app.celery_app"
elif [ -f "services/worker-service/celery_app.py" ]; then
    CELERY_APP="services.worker-service.celery_app"
else
    echo "⚠️  Nu pot găsi Celery app. Verifică structura proiectului."
    exit 1
fi

echo "   Folosind Celery app: $CELERY_APP"

# Pornește worker-ul în background
nohup celery -A $CELERY_APP worker \
    --loglevel=info \
    --logfile=logs/celery-worker.log \
    --detach \
    --pidfile=logs/celery-worker.pid

sleep 3

# Verifică dacă worker-ul rulează
if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ✅ Celery Worker pornit!"
    echo "   PID: $(pgrep -f 'celery.*worker' | head -1)"
else
    echo "   ❌ Celery Worker nu pornește"
    echo "   Verifică logurile: tail -f logs/celery-worker.log"
    exit 1
fi

echo ""
echo "✅ Celery Worker configurat!"
echo ""
echo "📋 Comenzi utile:"
echo "   tail -f logs/celery-worker.log  - Vezi logurile"
echo "   celery -A $CELERY_APP inspect active  - Verifică task-uri active"
echo "   pkill -f 'celery.*worker'  - Oprește worker-ul"
echo ""

