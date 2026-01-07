# Quick Start - Microservicii

## Setup Rapid

### 1. Instalare Dependențe

```bash
# Instalează Redis
brew install redis
brew services start redis

# Verifică Redis
redis-cli ping  # Ar trebui să returneze: PONG
```

### 2. Configurare Variabile de Mediu

Creează `.env` în root:
```env
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
```

### 3. Instalare Dependențe pentru Fiecare Serviciu

```bash
# Sheets Service
cd services/sheets-service
pip install -r requirements.txt
cd ../..

# Scraper Service
cd services/scraper-service
pip install -r requirements.txt
playwright install chromium  # Instalează browser-ul pentru Playwright
cd ../..

# API Service
cd services/api-service
pip install -r requirements.txt
cd ../..

# Worker Service
cd services/worker-service
pip install -r requirements.txt
cd ../..
```

### 4. Pornire Servicii

**Opțiunea 1: Script automat**
```bash
./scripts/start_all_services.sh
```

**Opțiunea 2: Manual**
```bash
# Terminal 1 - Sheets Service
cd services/sheets-service
python main.py

# Terminal 2 - Scraper Service
cd services/scraper-service
python main.py

# Terminal 3 - API Service
cd services/api-service
python main.py

# Terminal 4 - Worker Service
cd services/worker-service
celery -A celery_app worker --loglevel=info
```

### 5. Verificare

```bash
# Health checks
curl http://localhost:8001/health  # sheets-service
curl http://localhost:8002/health  # scraper-service
curl http://localhost:5001/health  # api-service

# Test API
curl http://localhost:5001/api/worksheets
curl http://localhost:5001/api/rankings?worksheet=Crime%20Fiction%20-%20US
```

## Docker (Production)

```bash
# Build și start toate serviciile
docker-compose -f docker/docker-compose.yml up -d

# Verifică status
docker-compose -f docker/docker-compose.yml ps

# Logs
docker-compose -f docker/docker-compose.yml logs -f
```

## Structura Logs

Logs pentru fiecare serviciu în `logs/`:
- `logs/sheets-service.log`
- `logs/scraper-service.log`
- `logs/api-service.log`
- `logs/worker-service.log`

## Next Steps

1. Verifică că toate serviciile rulează: `./scripts/start_all_services.sh`
2. Testează API-ul: `curl http://localhost:5001/api/worksheets`
3. Verifică logs pentru erori: `tail -f logs/*.log`
4. Citește documentația completă: `README_MICROSERVICES.md`

