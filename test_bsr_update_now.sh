#!/bin/bash
# Script pentru test imediat al BSR update pe EC2

echo "🧪 Test BSR Update - Declanșare Imediată"
echo "=========================================="
echo ""

# URL-ul aplicației (local pe EC2)
API_URL="http://localhost:5001"

# Test 1: Declanșează update pentru UK
echo "1️⃣  Declanșare update pentru 'Crime Fiction - UK'..."
UK_RESPONSE=$(curl -s -X POST "$API_URL/api/trigger-bsr-update" \
  -H "Content-Type: application/json" \
  -d '{"worksheet": "Crime Fiction - UK"}')

echo "   Răspuns: $UK_RESPONSE"
echo ""

# Așteaptă 2 secunde
sleep 2

# Test 2: Declanșează update pentru US
echo "2️⃣  Declanșare update pentru 'Crime Fiction - US'..."
US_RESPONSE=$(curl -s -X POST "$API_URL/api/trigger-bsr-update" \
  -H "Content-Type: application/json" \
  -d '{"worksheet": "Crime Fiction - US"}')

echo "   Răspuns: $US_RESPONSE"
echo ""

# Verifică statusul Celery (dacă este disponibil)
echo "3️⃣  Verificare procese Celery..."
ps aux | grep "celery.*worker" | grep -v grep
echo ""

# Verifică logurile recente
echo "4️⃣  Ultimele loguri (ultimele 20 linii):"
sudo journalctl -u books-reporting -n 20 --no-pager | tail -20
echo ""

echo "✅ Test declanșat!"
echo ""
echo "📝 Pentru a urmări progresul în timp real:"
echo "   sudo journalctl -u books-reporting -f"
echo ""
echo "   SAU"
echo ""
echo "   tail -f /home/ec2-user/app/books-reporting/logs/celery-worker.log"

