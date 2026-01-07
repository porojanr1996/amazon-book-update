#!/bin/bash
# Script pentru pornirea serverului Flask

cd "$(dirname "$0")"
source venv/bin/activate

echo "🚀 Pornire server Flask..."
echo "📂 Director: $(pwd)"
echo ""

# Verifică dacă Redis rulează
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  Redis nu rulează!"
    echo "📦 Pornire Redis..."
    brew services start redis 2>/dev/null || redis-server &
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "✅ Redis pornit cu succes!"
    else
        echo "❌ Eroare la pornirea Redis. Verifică manual: redis-cli ping"
        echo "💡 Instalează Redis: brew install redis"
        echo "💡 Pornește Redis: brew services start redis"
    fi
else
    echo "✅ Redis rulează deja"
fi

echo ""

# Oprește serverul dacă rulează deja
if lsof -ti:5001 > /dev/null 2>&1; then
    echo "⚠️  Oprire server existent..."
    lsof -ti:5001 | xargs kill -9
    sleep 1
fi

# Pornește serverul
echo "✅ Pornire server pe portul 5001..."
echo "🌐 Site-ul va fi disponibil la: http://localhost:5001"
echo ""
echo "📋 Pentru a opri serverul: Apasă CTRL+C"
echo ""

python3 app.py

