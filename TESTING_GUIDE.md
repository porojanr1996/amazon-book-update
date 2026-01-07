# Ghid de Testare Microservicii

## Testare Pas cu Pas

### 1. Testare Sheets Service

```bash
cd services/sheets-service
source ../../venv/bin/activate
python main.py
```

În alt terminal:
```bash
# Health check
curl http://localhost:8001/health

# Get worksheets
curl http://localhost:8001/api/worksheets

# Get books
curl "http://localhost:8001/api/books?worksheet=Crime%20Fiction%20-%20US"
```

**Expected:** JSON responses cu datele din Google Sheets

### 2. Testare Scraper Service

```bash
cd services/scraper-service
source ../../venv/bin/activate
python main.py
```

În alt terminal:
```bash
# Health check
curl http://localhost:8002/health

# Extract BSR
curl -X POST http://localhost:8002/api/extract-bsr \
  -H "Content-Type: application/json" \
  -d '{"amazon_url": "https://www.amazon.com/dp/B07QJD3B7S", "use_playwright": false}'

# Extract cover
curl -X POST http://localhost:8002/api/extract-cover \
  -H "Content-Type: application/json" \
  -d '{"amazon_url": "https://www.amazon.com/dp/B07QJD3B7S", "use_playwright": true}'
```

**Expected:** JSON cu BSR sau cover URL

### 3. Testare API Service

```bash
cd services/api-service
source ../../venv/bin/activate
python main.py
```

În alt terminal:
```bash
# Health check
curl http://localhost:5001/health

# Get worksheets (proxy)
curl http://localhost:5001/api/worksheets

# Get rankings
curl "http://localhost:5001/api/rankings?worksheet=Crime%20Fiction%20-%20US"

# Get chart data
curl "http://localhost:5001/api/chart-data?range=30&worksheet=Crime%20Fiction%20-%20US"
```

**Expected:** JSON responses cu date agregate

### 4. Testare Worker Service

```bash
cd services/worker-service
source ../../venv/bin/activate
celery -A celery_app worker --loglevel=info
```

În alt terminal (Python):
```python
from services.worker_service.celery_app import celery_app
from services.worker_service.tasks import update_worksheet_bsr

# Enqueue task
result = update_worksheet_bsr.delay("Crime Fiction - US")
print(f"Task ID: {result.id}")

# Check status
print(result.status)
print(result.get())  # Wait for result
```

**Expected:** Task se execută și returnează rezultate

## Testare Automată

Rulează scriptul de testare:
```bash
./test_services.sh
```

Acest script:
1. Verifică Redis
2. Testează fiecare serviciu individual
3. Verifică health checks
4. Testează endpoints principale
5. Oprește serviciile la final

## Verificare Logs

```bash
# Sheets Service
tail -f logs/sheets-service-test.log

# Scraper Service
tail -f logs/scraper-service-test.log

# API Service
tail -f logs/api-service-test.log

# Worker Service
tail -f logs/worker-service-test.log
```

## Troubleshooting

### Service nu pornește
1. Verifică logs pentru erori
2. Verifică dacă portul este liber: `lsof -i :<port>`
3. Verifică dependențe: `pip install -r requirements.txt`

### Service nu răspunde
1. Verifică health check: `curl http://localhost:<port>/health`
2. Verifică logs pentru erori
3. Verifică că serviciile dependente rulează

### Erori de comunicare între servicii
1. Verifică variabilele de mediu: `SHEETS_SERVICE_URL`, `SCRAPER_SERVICE_URL`
2. Verifică că serviciile sunt pornite
3. Verifică network/firewall settings

## Rezultate Testare

Vezi `TEST_RESULTS.md` pentru rezultatele testării complete.

