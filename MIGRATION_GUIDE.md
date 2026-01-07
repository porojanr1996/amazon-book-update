# Ghid de Migrare la Microservicii

## Structura Nouă

Proiectul a fost reorganizat în microservicii pentru ușurință de întreținere și debugging.

## Servicii Create

### 1. shared/ - Cod Comun
- `shared/config/` - Configurație comună
- `shared/models/` - Pydantic models
- `shared/utils/` - Utilities (logger, bsr_parser)

### 2. services/sheets-service/
- Google Sheets operations
- Port: 8001
- Endpoints: `/api/worksheets`, `/api/books`, `/api/update-bsr`, etc.

### 3. services/scraper-service/
- Amazon scraping (BSR + covers)
- Port: 8002
- Endpoints: `/api/extract-bsr`, `/api/extract-cover`

### 4. services/api-service/
- Web API pentru frontend
- Port: 5001
- Endpoints: `/api/rankings`, `/api/chart-data`

### 5. services/worker-service/
- Background jobs (Celery)
- Port: 8003
- Tasks: `bsr.update_worksheet`, `covers.extract_all`

## Pași de Migrare

### Pasul 1: Setup Shared Code
```bash
# Shared code este deja creat în shared/
# Nu necesită acțiuni suplimentare
```

### Pasul 2: Setup Sheets Service
```bash
cd services/sheets-service
pip install -r requirements.txt
python main.py
```

### Pasul 3: Setup Scraper Service
```bash
cd services/scraper-service
pip install -r requirements.txt
python main.py
```

### Pasul 4: Setup API Service
```bash
cd services/api-service
pip install -r requirements.txt
python main.py
```

### Pasul 5: Setup Worker Service
```bash
cd services/worker-service
pip install -r requirements.txt
celery -A celery_app worker --loglevel=info
```

## Comunicare între Servicii

### Development (Local)
- Serviciile comunică prin HTTP pe localhost
- Configurare în `shared/config/__init__.py`

### Production (Docker)
- Serviciile comunică prin numele containerelor
- Configurare în `docker-compose.yml`

## Variabile de Mediu

Creează `.env` în root cu:
```env
# Service URLs (pentru inter-service communication)
SHEETS_SERVICE_URL=http://localhost:8001
SCRAPER_SERVICE_URL=http://localhost:8002

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id
```

## Testing

### Test Individual Service
```bash
# Test sheets-service
curl http://localhost:8001/health

# Test scraper-service
curl http://localhost:8002/health

# Test api-service
curl http://localhost:5001/health
```

### Test Integration
```bash
# Test full flow
curl http://localhost:5001/api/rankings?worksheet=Crime%20Fiction%20-%20US
```

## Beneficii

1. **Separare responsabilități** - Fiecare serviciu are un scop clar
2. **Debugging ușor** - Logs separate pentru fiecare serviciu
3. **Scalare independentă** - Poți scala fiecare serviciu separat
4. **Deployment independent** - Poți deploya servicii fără să afectezi altele
5. **Testare izolată** - Poți testa fiecare serviciu separat

## Next Steps

1. Completează migrarea tuturor serviciilor
2. Creează Docker configs pentru fiecare serviciu
3. Creează docker-compose.yml pentru orchestration
4. Adaugă monitoring și health checks
5. Documentează API-urile fiecărui serviciu

