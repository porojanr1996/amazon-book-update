#!/bin/bash
# Script de diagnostic rapid pentru aplicație

echo "=== 🔍 Diagnostic Rapid Aplicație ==="
echo ""

echo "1️⃣  Serviciul systemd:"
if sudo systemctl is-active books-reporting > /dev/null 2>&1; then
    echo "   ✅ Serviciul rulează"
    sudo systemctl status books-reporting --no-pager -l | head -n 5
else
    echo "   ❌ Serviciul NU rulează"
fi
echo ""

echo "2️⃣  Procese Python/FastAPI:"
PROCESSES=$(ps aux | grep -E "(uvicorn|python.*main|fastapi)" | grep -v grep)
if [ -n "$PROCESSES" ]; then
    echo "   ✅ Procese găsite:"
    echo "$PROCESSES" | head -n 3
else
    echo "   ❌ Nu există procese Python/FastAPI"
fi
echo ""

echo "3️⃣  Port 5001:"
PORT_CHECK=$(sudo ss -tlnp 2>/dev/null | grep 5001 || sudo netstat -tlnp 2>/dev/null | grep 5001)
if [ -n "$PORT_CHECK" ]; then
    echo "   ✅ Port 5001 este în uz:"
    echo "$PORT_CHECK"
else
    echo "   ❌ Port 5001 NU este în uz"
fi
echo ""

echo "4️⃣  Test local (localhost):"
LOCAL_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/api/scheduler-status 2>/dev/null)
if [ "$LOCAL_TEST" = "200" ]; then
    echo "   ✅ Aplicația răspunde local (HTTP $LOCAL_TEST)"
    curl -s http://localhost:5001/api/scheduler-status | head -c 100
    echo "..."
else
    echo "   ❌ Aplicația NU răspunde local (HTTP $LOCAL_TEST)"
fi
echo ""

echo "5️⃣  Test IP public (din interior):"
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null)
if [ -n "$PUBLIC_IP" ]; then
    echo "   IP Public: $PUBLIC_IP"
    PUBLIC_TEST=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 http://$PUBLIC_IP:5001/api/scheduler-status 2>/dev/null)
    if [ "$PUBLIC_TEST" = "200" ]; then
        echo "   ✅ Aplicația răspunde la IP public (HTTP $PUBLIC_TEST)"
    else
        echo "   ⚠️  Aplicația NU răspunde la IP public (HTTP $PUBLIC_TEST)"
        echo "   (Poate fi normal dacă Security Group blochează)"
    fi
else
    echo "   ⚠️  Nu pot obține IP public"
fi
echo ""

echo "6️⃣  Ultimele erori din loguri:"
ERRORS=$(sudo journalctl -u books-reporting -n 20 --no-pager 2>/dev/null | grep -i error | tail -n 3)
if [ -n "$ERRORS" ]; then
    echo "   ⚠️  Erori găsite:"
    echo "$ERRORS"
else
    echo "   ✅ Nu există erori recente"
fi
echo ""

echo "7️⃣  Redis:"
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis rulează"
else
    echo "   ❌ Redis NU rulează"
fi
echo ""

echo "8️⃣  Celery Worker:"
if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ✅ Celery Worker rulează"
    echo "   PID: $(pgrep -f 'celery.*worker' | head -1)"
else
    echo "   ⚠️  Celery Worker NU rulează (poate fi normal dacă nu este necesar)"
fi
echo ""

echo "=== ✅ Diagnostic Complet ==="
echo ""
echo "📋 Rezumat:"
echo "   - Dacă serviciul rulează dar nu răspunde: verifică Security Group"
echo "   - Dacă serviciul nu rulează: sudo systemctl restart books-reporting"
echo "   - Dacă portul nu este în uz: verifică configurația aplicației"

