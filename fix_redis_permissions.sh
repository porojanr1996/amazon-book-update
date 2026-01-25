#!/bin/bash
# Fix permisiuni Redis pe EC2

echo "🔧 Fix permisiuni Redis..."

# Opțiunea 1: Setează permisiuni pentru directoarele Redis
sudo mkdir -p /etc/redis /var/lib/redis /var/log/redis
sudo chown -R ec2-user:ec2-user /var/lib/redis /var/log/redis
sudo chmod -R 755 /var/lib/redis /var/log/redis

# Sau Opțiunea 2: Folosește directoare în home (mai simplu)
REDIS_HOME_DIR="$HOME/redis"
mkdir -p "$REDIS_HOME_DIR/data" "$REDIS_HOME_DIR/logs"

echo "✅ Permisiuni setate"
echo ""
echo "Acum pornește Redis cu:"
echo "  redis-server /etc/redis/redis.conf"
echo ""
echo "Sau dacă tot nu funcționează, folosește configurația din home:"
echo "  redis-server --daemonize yes --dir $REDIS_HOME_DIR/data --logfile $REDIS_HOME_DIR/logs/redis.log"

