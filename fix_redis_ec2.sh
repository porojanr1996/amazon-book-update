#!/bin/bash
# Script pentru instalare și configurare Redis pe EC2

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

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
        echo "   ⚠️  Redis nu este în repo-uri standard pentru Amazon Linux 2023"
        echo "   Compilare Redis din sursă..."
        
        # Instalează dependențele pentru compilare
        if command -v dnf > /dev/null 2>&1; then
            echo "   Instalare dependențe (gcc, make, wget/tar)..."
            sudo dnf install -y gcc make wget tar 2>/dev/null || sudo dnf install -y gcc make curl tar 2>/dev/null || {
                echo "   ⚠️  Nu pot instala dependențele automat"
                echo "   Instalează manual: sudo dnf install -y gcc make wget tar"
                exit 1
            }
        else
            echo "   Instalare dependențe (gcc, make, wget/tar)..."
            sudo yum install -y gcc make wget tar 2>/dev/null || sudo yum install -y gcc make curl tar 2>/dev/null || {
                echo "   ⚠️  Nu pot instala dependențele automat"
                echo "   Instalează manual: sudo yum install -y gcc make wget tar"
                exit 1
            }
        fi
        
        # Descarcă și compilează Redis
        echo "   Descărcare Redis..."
        cd /tmp
        if command -v wget > /dev/null 2>&1; then
            wget https://download.redis.io/redis-stable.tar.gz || {
                echo "   ⚠️  wget a eșuat, încerc cu curl..."
                curl -L -o redis-stable.tar.gz https://download.redis.io/redis-stable.tar.gz || {
                    echo "   ❌ Nu pot descărca Redis"
                    exit 1
                }
            }
        else
            curl -L -o redis-stable.tar.gz https://download.redis.io/redis-stable.tar.gz || {
                echo "   ❌ Nu pot descărca Redis"
                exit 1
            }
        fi
        
        echo "   Dezarhivare..."
        tar xzf redis-stable.tar.gz || {
            echo "   ❌ Nu pot dezarhiva Redis"
            exit 1
        }
        
        cd redis-stable
        echo "   Compilare Redis (poate dura câteva minute)..."
        make || {
            echo "   ❌ Compilarea a eșuat"
            exit 1
        }
        
        echo "   Instalare Redis..."
        sudo make install || {
            echo "   ❌ Instalarea a eșuat"
            exit 1
        }
        
        # Creează directoarele pentru configurare
        echo "   Configurare Redis..."
        sudo mkdir -p /etc/redis
        sudo mkdir -p /var/lib/redis
        sudo mkdir -p /var/log/redis
        
        # Copiază și configurează redis.conf
        if [ -f redis.conf ]; then
            sudo cp redis.conf /etc/redis/redis.conf
            sudo sed -i 's/^daemonize no/daemonize yes/' /etc/redis/redis.conf
            sudo sed -i 's|^dir ./|dir /var/lib/redis|' /etc/redis/redis.conf
            sudo sed -i 's|^logfile ""|logfile /var/log/redis/redis.log|' /etc/redis/redis.conf
        fi
        
        cd "$SCRIPT_DIR"
        echo "   ✅ Redis compilat și instalat cu succes!"
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
        REDIS_SERVER=$(which redis-server 2>/dev/null || find /usr -name redis-server 2>/dev/null || find /usr/local -name redis-server 2>/dev/null | head -1)
        
        if [ -n "$REDIS_SERVER" ]; then
            echo "   Găsit redis-server la: $REDIS_SERVER"
            # Folosește configurația dacă există
            if [ -f /etc/redis/redis.conf ]; then
                nohup $REDIS_SERVER /etc/redis/redis.conf > /dev/null 2>&1 &
            else
                nohup $REDIS_SERVER --daemonize yes > /dev/null 2>&1 &
            fi
            sleep 2
        else
            echo "   ❌ Nu pot găsi redis-server"
            echo "   Verifică dacă compilarea a reușit"
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

