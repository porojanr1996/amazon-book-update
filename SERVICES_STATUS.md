# Status Servicii - Live

## Servicii Rulează

### Sheets Service
- **Port:** 8001
- **Status:** Running
- **Health:** http://localhost:8001/health
- **Logs:** `logs/sheets-service.log`

### Scraper Service
- **Port:** 8002
- **Status:** Running
- **Health:** http://localhost:8002/health
- **Logs:** `logs/scraper-service.log`

### API Service
- **Port:** 5001
- **Status:** Running
- **Health:** http://localhost:5001/health
- **Dashboard:** http://localhost:5001/
- **Logs:** `logs/api-service.log`

### Worker Service
- **Status:** Running
- **Logs:** `logs/worker-service.log`

## Comenzi Utile

### Verificare Status
```bash
# Health checks
curl http://localhost:8001/health  # Sheets
curl http://localhost:8002/health  # Scraper
curl http://localhost:5001/health   # API

# Test endpoints
curl http://localhost:5001/api/worksheets
curl "http://localhost:5001/api/rankings?worksheet=Crime%20Fiction%20-%20US"
```

### Verificare Logs
```bash
tail -f logs/sheets-service.log
tail -f logs/scraper-service.log
tail -f logs/api-service.log
tail -f logs/worker-service.log
```

### Oprire Servicii
```bash
# Găsește PIDs
lsof -ti:8001,8002,5001

# Oprește toate
lsof -ti:8001,8002,5001 | xargs kill

# Sau oprește worker separat
pkill -f "celery.*celery_app"
```

## Testare Rapidă

```bash
# Test complet
./test_services.sh

# Sau manual
curl http://localhost:5001/api/worksheets
curl "http://localhost:5001/api/rankings?worksheet=Crime%20Fiction%20-%20US"
```

