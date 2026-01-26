#!/bin/bash
# Script pentru a declanșa update-uri BSR pentru UK și US

echo "🔄 Declanșare Update BSR pentru UK și US"
echo ""

# URL-ul aplicației
API_URL="http://localhost:5001"

# Verifică dacă aplicația rulează
if ! curl -s "$API_URL/api/scheduler-status" > /dev/null 2>&1; then
    echo "❌ Aplicația nu răspunde la $API_URL"
    echo "   Verifică: sudo systemctl status books-reporting"
    exit 1
fi

echo "✅ Aplicația rulează"
echo ""

# Worksheets
WORKSHEETS=("Crime Fiction - UK" "Crime Fiction - US")

echo "📚 Worksheets de actualizat:"
for ws in "${WORKSHEETS[@]}"; do
    echo "   - $ws"
done
echo ""

# Declanșează update pentru fiecare worksheet
SUCCESS_COUNT=0
FAILED_COUNT=0

for worksheet in "${WORKSHEETS[@]}"; do
    echo "🚀 Declanșare update pentru: $worksheet..."
    
    RESPONSE=$(curl -s -X POST "$API_URL/api/trigger-bsr-update" \
        -H "Content-Type: application/json" \
        -d "{\"worksheet\": \"$worksheet\"}")
    
    if echo "$RESPONSE" | grep -q '"status":"started"'; then
        echo "   ✅ Update declanșat cu succes pentru $worksheet"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo "   ❌ Eroare la declanșare update pentru $worksheet"
        echo "   Răspuns: $RESPONSE"
        FAILED_COUNT=$((FAILED_COUNT + 1))
    fi
    echo ""
    
    # Mic delay între request-uri
    sleep 1
done

echo "=" * 60
echo "📊 Rezumat:"
echo "   ✅ Succes: $SUCCESS_COUNT"
if [ $FAILED_COUNT -gt 0 ]; then
    echo "   ❌ Erori: $FAILED_COUNT"
fi
echo "=" * 60
echo ""
echo "📝 Update-urile rulează în background."
echo "   Monitorizează progresul:"
echo "   sudo journalctl -u books-reporting -f"
echo ""
echo "   SAU"
echo "   tail -f logs/celery-worker.log"
echo ""

