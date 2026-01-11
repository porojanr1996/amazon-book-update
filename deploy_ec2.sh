#!/bin/bash
# Script optimizat pentru deployment pe EC2
# Construiește imaginea manual, apoi folosește docker-compose simplu

set -e

echo "🚀 Deployment optimizat pentru EC2"
echo "===================================="

cd /home/ec2-user/app/books-reporting

# Setează environment variables
export GOOGLE_SHEETS_SPREADSHEET_ID=${GOOGLE_SHEETS_SPREADSHEET_ID:-1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA}

echo ""
echo "📦 Pasul 1: Construire imagine Docker (fără buildx)..."
sudo docker build -t books-reporting-app:latest -f Dockerfile .

echo ""
echo "🛑 Pasul 2: Oprește serviciile vechi..."
sudo docker-compose -f docker/docker-compose.yml down 2>/dev/null || true
sudo docker-compose -f docker/docker-compose-simple.yml down 2>/dev/null || true

echo ""
echo "🚀 Pasul 3: Pornește serviciile (Redis + API)..."
sudo docker-compose -f docker/docker-compose-simple.yml up -d

echo ""
echo "⏳ Așteaptă 10 secunde pentru inițializare..."
sleep 10

echo ""
echo "✅ Status servicii:"
sudo docker ps

echo ""
echo "📋 Logs API service (ultimele 20 linii):"
sudo docker logs docker-api-service-1 --tail 20 2>/dev/null || echo "Container nu rulează încă"

echo ""
echo "🌐 Testează aplicația:"
echo "   curl http://localhost:5001/health"
echo "   sau: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5001/health"

