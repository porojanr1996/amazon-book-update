#!/bin/bash
# Test SSH connection și comenzi pas cu pas

echo "🔍 Testare conexiune SSH..."
ssh -i /tmp/ec2_key.pem -o StrictHostKeyChecking=no -o ConnectTimeout=10 ec2-user@16.171.115.88 "echo '✅ Conectat la EC2'; whoami; pwd" 2>&1

echo ""
echo "🔍 Testare docker-compose..."
ssh -i /tmp/ec2_key.pem -o StrictHostKeyChecking=no ec2-user@16.171.115.88 "cd /home/ec2-user/app/books-reporting && sudo docker-compose -f docker/docker-compose.yml ps 2>&1" | head -20

