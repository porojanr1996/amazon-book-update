#!/bin/bash
# Script pentru verificare status complet al serviciului

echo "📊 Verificare Status Serviciu Books Reporting"
echo "=============================================="
echo ""

# 1. Verifică statusul systemd
echo "1️⃣  Status Systemd Service:"
sudo systemctl is-active books-reporting && echo "   ✅ Serviciul este ACTIV" || echo "   ⚠️  Serviciul NU este activ"
echo ""

# 2. Verifică procesul pe portul 5001
echo "2️⃣  Proces pe Portul 5001:"
PID=$(sudo lsof -ti:5001 2>/dev/null)
if [ -n "$PID" ]; then
    echo "   ✅ Proces găsit: PID $PID"
    ps aux | grep $PID | grep -v grep
else
    echo "   ⚠️  Nu s-a găsit proces pe portul 5001"
fi
echo ""

# 3. Testează răspunsul aplicației
echo "3️⃣  Test Răspuns Aplicație:"
RESPONSE=$(curl -s http://localhost:5001/api/scheduler-status 2>/dev/null)
if [ $? -eq 0 ] && [ -n "$RESPONSE" ]; then
    echo "   ✅ Aplicația răspunde corect"
    echo "   📋 Răspuns:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
    echo "   ❌ Aplicația NU răspunde"
fi
echo ""

# 4. Verifică Celery worker
echo "4️⃣  Celery Worker:"
if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ✅ Celery Worker rulează"
    ps aux | grep "celery.*worker" | grep -v grep | head -1
else
    echo "   ⚠️  Celery Worker NU rulează (poate nu este necesar)"
fi
echo ""

# 5. Verifică Redis
echo "5️⃣  Redis:"
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis rulează"
else
    echo "   ❌ Redis NU rulează"
fi
echo ""

# 6. Ultimele loguri
echo "6️⃣  Ultimele Loguri (ultimele 10 linii):"
sudo journalctl -u books-reporting -n 10 --no-pager | tail -10
echo ""

echo "✅ Verificare completă!"

