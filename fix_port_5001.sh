#!/bin/bash
# Script pentru a opri procesul care folosește portul 5001 și a reporni serviciul

echo "🔍 Găsire proces care folosește portul 5001..."

# Găsește PID-ul procesului care folosește portul 5001
PID=$(sudo lsof -ti:5001 2>/dev/null || sudo ss -tlnp | grep :5001 | awk '{print $6}' | cut -d',' -f2 | cut -d'=' -f2 | head -1)

if [ -z "$PID" ]; then
    echo "⚠️  Nu s-a găsit proces care folosește portul 5001"
    echo "   Poate că portul este deja liber."
else
    echo "📋 Proces găsit: PID $PID"
    echo "   Oprire proces..."
    sudo kill -9 $PID 2>/dev/null || true
    sleep 2
    echo "✅ Proces oprit"
fi

# Oprește și serviciul systemd pentru a fi sigur
echo ""
echo "🛑 Oprire serviciul books-reporting..."
sudo systemctl stop books-reporting
sleep 3

# Verifică dacă mai sunt procese Python care rulează
echo ""
echo "🧹 Curățare procese Python rămase..."
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true
sleep 2

# Verifică din nou portul
echo ""
echo "🔍 Verificare port 5001..."
if sudo lsof -ti:5001 >/dev/null 2>&1; then
    echo "⚠️  Portul 5001 este încă folosit. Încercare forțată..."
    sudo fuser -k 5001/tcp 2>/dev/null || true
    sleep 2
else
    echo "✅ Portul 5001 este liber"
fi

# Repornește serviciul
echo ""
echo "🚀 Repornire serviciul books-reporting..."
sudo systemctl start books-reporting
sleep 3

# Verifică statusul
echo ""
echo "📊 Status serviciu:"
sudo systemctl status books-reporting --no-pager -l

echo ""
echo "✅ Gata! Verifică logurile cu:"
echo "   sudo journalctl -u books-reporting -f"

