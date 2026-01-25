#!/bin/bash
# Script pentru instalare și configurare Redis pe EC2

set -e

echo "🔴 Instalare și configurare Redis pe EC2..."
echo ""

# Verifică dacă Redis este deja instalat
if command -v redis-cli > /dev/null 2>&1; then
    echo "✅ Redis este deja instalat"
    REDIS_INSTALLED=true
else
    echo "📦 Instalare Redis..."
    
    # Detectează OS
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
    else
        echo "❌ Nu pot detecta OS-ul"
        exit 1
    fi
    
    # Instalează Redis în funcție de OS
    if [ "$OS" = "amzn" ] || [ "$OS" = "rhel" ] || [ "$OS" = "centos" ]; then
        # Amazon Linux / RHEL / CentOS
        echo "   Detected: Amazon Linux / RHEL / CentOS"
        sudo yum update -y
        sudo yum install -y redis
    elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
        # Ubuntu / Debian
        echo "   Detected: Ubuntu / Debian"
        sudo apt-get update
        sudo apt-get install -y redis-server
    else
        echo "⚠️  OS necunoscut: $OS"
        echo "   Încearcă manual:"
        echo "   - Amazon Linux: sudo yum install -y redis"
        echo "   - Ubuntu: sudo apt-get install -y redis-server"
        exit 1
    fi
    
    REDIS_INSTALLED=true
fi

if [ "$REDIS_INSTALLED" = true ]; then
    echo ""
    echo "🚀 Pornire Redis..."
    
    # Încearcă să pornească ca systemd service
    if sudo systemctl start redis 2>/dev/null || sudo systemctl start redis-server 2>/dev/null; then
        echo "   ✅ Redis pornit ca systemd service"
        sudo systemctl enable redis 2>/dev/null || sudo systemctl enable redis-server 2>/dev/null || true
    else
        # Dacă nu funcționează systemd, pornește manual
        echo "   ⚠️  Systemd service nu funcționează, pornire manuală..."
        
        # Găsește redis-server
        REDIS_SERVER=$(which redis-server 2>/dev/null || find /usr -name redis-server 2>/dev/null | head -1)
        
        if [ -n "$REDIS_SERVER" ]; then
            echo "   Găsit redis-server la: $REDIS_SERVER"
            nohup $REDIS_SERVER --daemonize yes > /dev/null 2>&1 &
            sleep 2
        else
            echo "   ❌ Nu pot găsi redis-server"
            exit 1
        fi
    fi
    
    echo ""
    echo "🔍 Verificare Redis..."
    sleep 2
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "   ✅ Redis rulează!"
        redis-cli ping
    else
        echo "   ❌ Redis nu răspunde"
        echo ""
        echo "   Încearcă manual:"
        echo "   redis-server --daemonize yes"
        echo "   sau"
        echo "   sudo systemctl start redis"
        exit 1
    fi
fi

echo ""
echo "✅ Redis configurat și pornit!"
echo ""
echo "📋 Comenzi utile:"
echo "   redis-cli ping          - Verifică dacă Redis rulează"
echo "   redis-cli info          - Informații despre Redis"
echo "   sudo systemctl status redis  - Status Redis service"
echo ""

