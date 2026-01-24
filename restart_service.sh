#!/bin/bash
# Script pentru restart complet al serviciului pe EC2

echo "🔄 Restart complet al serviciului books-reporting..."

# Oprește serviciul
sudo systemctl stop books-reporting

# Șterge cache-ul Python
find /home/ec2-user/app/books-reporting -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
find /home/ec2-user/app/books-reporting -type f -name "*.pyc" -delete 2>/dev/null || true

# Actualizează codul
cd /home/ec2-user/app/books-reporting
git pull origin main

# Repornește serviciul
sudo systemctl start books-reporting

# Verifică statusul
sleep 3
sudo systemctl status books-reporting --no-pager

echo "✅ Restart complet!"

