#!/bin/bash
# Script simplu pentru pornirea tuturor serviciilor
# Rulează scraping-ul zilnic la 10:00 AM (ora României)

cd "$(dirname "$0")"

echo "🚀 Pornire servicii books-reporting..."
echo ""

# Rulează scriptul de restart (care oprește și repornește totul)
./restart_all_services.sh

echo ""
echo "✅ Gata! Serviciile rulează."
echo ""
echo "📋 Comenzi utile:"
echo "   ./restart_all_services.sh  - Restart toate serviciile"
echo "   tail -f logs/fastapi.log  - Vezi logurile FastAPI"
echo "   curl http://localhost:5001/api/scheduler-status  - Verifică status scheduler"
echo ""

