#!/bin/bash
# Script pentru extragerea cover images pentru toate cărțile

echo "📸 Extragere cover images pentru cărți..."
echo ""

# Așteaptă puțin pentru a se asigura că serverul este gata
sleep 2

# Extrage cover images pentru worksheet-ul default
curl -X POST http://127.0.0.1:5001/api/extract-covers \
  -H "Content-Type: application/json" \
  -d '{"worksheet": "Crime Fiction - US"}' \
  | python3 -m json.tool

echo ""
echo "✅ Comanda trimisă! Verifică log-urile serverului pentru progres."
echo "💡 Cover images vor apărea pe site după ce extragerea este finalizată."

