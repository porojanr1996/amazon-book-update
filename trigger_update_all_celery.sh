#!/bin/bash
# Script pentru a declanșa update pentru TOATE worksheets folosind Celery

echo "🔄 Declanșare Update BSR pentru TOATE Worksheets (Celery)"
echo ""

cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# Verifică Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "❌ Redis nu rulează!"
    exit 1
fi

echo "✅ Redis rulează"
echo ""

# Verifică Celery Worker
if ! pgrep -f "celery.*worker" > /dev/null; then
    echo "⚠️  Celery Worker nu rulează!"
    echo "   Pornește worker-ul: ./start_celery_worker_ec2.sh"
    exit 1
fi

echo "✅ Celery Worker rulează"
echo ""

# Declanșează update pentru toate worksheets
echo "🚀 Declanșare update pentru toate worksheets..."
echo ""

python3 << EOF
from app.tasks.bsr_tasks import update_all_worksheets_bsr
import time

print("Sending task to Celery...")
result = update_all_worksheets_bsr.delay()
print(f"✅ Task ID: {result.id}")
print(f"   Task state: {result.state}")
print("")
print("📝 Task-ul rulează în background.")
print("   Monitorizează progresul:")
print("   tail -f logs/celery-worker.log")
print("")
print("   SAU verifică statusul:")
print(f"   python3 -c \"from app.tasks.bsr_tasks import update_all_worksheets_bsr; from app.celery_app import celery_app; result = celery_app.AsyncResult('{result.id}'); print('State:', result.state); print('Info:', result.info if result.info else 'N/A')\"")
EOF

echo ""
echo "✅ Update declanșat!"
echo ""

