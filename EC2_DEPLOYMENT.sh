#!/bin/bash
# Script complet de deployment pe EC2
# Configurează totul pentru UK și US scraping cu screenshots la ora 10:00 AM (ora României)

set -e

echo "🚀 Deployment complet pe EC2 pentru books-reporting"
echo "=================================================="
echo ""

# Variabile
APP_DIR="/home/ec2-user/app/books-reporting"
SERVICE_NAME="books-reporting"

# Verifică dacă suntem pe EC2
if [ ! -f "/sys/hypervisor/uuid" ] && [ ! -d "/var/lib/cloud/instance" ]; then
    echo "⚠️  Nu pare să fie un server EC2. Continuăm oricum..."
fi

echo "📂 Navigare la directorul aplicației..."
cd "$APP_DIR" || {
    echo "❌ Directorul $APP_DIR nu există!"
    echo "   Creează-l: mkdir -p $APP_DIR"
    exit 1
}

echo ""
echo "🔄 Pull ultimele modificări din Git..."
git pull origin main || {
    echo "⚠️  Git pull a eșuat. Verifică conexiunea sau rulează manual: git pull origin main"
}

echo ""
echo "🐍 Verificare Python și virtual environment..."
if [ ! -d "venv" ]; then
    echo "   Creare virtual environment..."
    python3 -m venv venv
fi

echo "   Activare virtual environment..."
source venv/bin/activate

echo ""
echo "📦 Instalare/actualizare dependențe..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "🔴 Verificare Redis..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "   Pornire Redis..."
    sudo systemctl start redis || redis-server --daemonize yes || {
        echo "⚠️  Redis nu pornește automat. Pornește-l manual:"
        echo "   sudo systemctl start redis"
        echo "   sau"
        echo "   redis-server --daemonize yes"
    }
else
    echo "   ✅ Redis rulează deja"
fi

echo ""
echo "🧹 Curățare cache Python..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

echo ""
echo "📝 Verificare variabile de mediu..."
if [ ! -f ".env" ]; then
    echo "⚠️  Fișierul .env nu există!"
    echo "   Creează-l cu:"
    echo "   cp env_template.txt .env"
    echo "   nano .env"
    echo ""
    echo "   Variabile importante:"
    echo "   - GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json"
    echo "   - GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id"
    echo "   - SCHEDULE_TIME=10:00"
    echo "   - SCHEDULE_TIMEZONE=Europe/Bucharest"
    echo ""
    read -p "   Continuăm fără .env? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "🛑 Oprire servicii existente..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true
sleep 2

echo ""
echo "⚙️  Configurare systemd service (dacă nu există)..."
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
if [ ! -f "$SERVICE_FILE" ]; then
    echo "   Creare service file..."
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Books Reporting FastAPI Application
After=network.target redis.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    echo "   ✅ Service creat și activat"
else
    echo "   ✅ Service există deja"
fi

echo ""
echo "🚀 Pornire servicii..."
sudo systemctl start $SERVICE_NAME
sleep 3

echo ""
echo "📊 Verificare status servicii..."
echo ""

# Verifică Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "   ✅ Redis: RUNNING"
else
    echo "   ❌ Redis: STOPPED"
fi

# Verifică FastAPI
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    echo "   ✅ FastAPI Service: RUNNING"
    echo "   🌐 URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):5001"
else
    echo "   ❌ FastAPI Service: STOPPED"
    echo "   Verifică logurile: sudo journalctl -u $SERVICE_NAME -n 50"
fi

# Verifică Celery (dacă este configurat)
if pgrep -f "celery.*worker" > /dev/null; then
    echo "   ✅ Celery Worker: RUNNING"
else
    echo "   ⚠️  Celery Worker: NOT RUNNING (poate nu este necesar)"
fi

echo ""
echo "✅ Deployment complet!"
echo ""
echo "📋 Configurație:"
echo "   - Scheduler: 10:00 AM (ora României - Europe/Bucharest)"
echo "   - UK scraping: ✅ Activ (detectare automată .co.uk)"
echo "   - US scraping: ✅ Activ (detectare automată amazon.com)"
echo "   - Metoda screenshots: ✅ Activ (OCR pentru BSR)"
echo ""
echo "🔍 Comenzi utile:"
echo "   sudo systemctl status $SERVICE_NAME"
echo "   sudo journalctl -u $SERVICE_NAME -f"
echo "   curl http://localhost:5001/api/scheduler-status"
echo ""
echo "📝 Logs:"
echo "   sudo journalctl -u $SERVICE_NAME -n 100"
echo ""

