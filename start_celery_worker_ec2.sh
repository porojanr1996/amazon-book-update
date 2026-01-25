#!/bin/bash
# Pornește Celery Worker pe EC2

cd /home/ec2-user/app/books-reporting

# Activează venv
source venv/bin/activate

# Verifică Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis nu rulează!"
    exit 1
fi

# Creează logs directory
mkdir -p logs

# Oprește worker-ul existent
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

# Pornește Celery Worker
echo "🚀 Pornire Celery Worker..."

# Găsește Celery app
if [ -f "app/tasks/bsr_tasks.py" ]; then
    CELERY_APP="app.tasks.bsr_tasks"
elif [ -f "app/celery_app.py" ]; then
    CELERY_APP="app.celery_app"
else
    echo "❌ Nu pot găsi Celery app"
    exit 1
fi

echo "   Folosind: $CELERY_APP"

# Pornește worker-ul în background
nohup celery -A $CELERY_APP worker \
    --loglevel=info \
    --logfile=logs/celery-worker.log \
    --detach \
    --pidfile=logs/celery-worker.pid

sleep 3

# Verifică
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
echo "   Logs: tail -f logs/celery-worker.log"

