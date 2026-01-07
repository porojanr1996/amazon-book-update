# 🚀 Cum să Pornești Serviciile

## Opțiunea 1: Script Automat (Recomandat)

```bash
cd /Users/testing/books-reporting
source venv/bin/activate
./scripts/start_all_services.sh
```

Acest script va:
1. ✅ Verifica Redis
2. ✅ Porni toate serviciile automat
3. ✅ Afișa PIDs și URLs

---

## Opțiunea 2: Manual (4 Terminale)

### Terminal 1 - Sheets Service
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/sheets-service
python3 main.py
```

### Terminal 2 - Scraper Service
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/scraper-service
python3 main.py
```

### Terminal 3 - API Service
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/api-service
python3 main.py
```

### Terminal 4 - Worker Service
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/worker-service
celery -A celery_app worker --loglevel=info
```

---

## Verificare Rapidă

După ce pornești serviciile, verifică:

```bash
# Health checks
curl http://localhost:8001/health  # Sheets
curl http://localhost:8002/health  # Scraper
curl http://localhost:5001/health  # API

# Dashboard
open http://localhost:5001/
```

---

## Oprire Servicii

```bash
# Oprește toate
lsof -ti:8001,8002,5001 | xargs kill
pkill -f "celery.*celery_app"
```

---

## Logs

```bash
tail -f logs/sheets-service.log
tail -f logs/scraper-service.log
tail -f logs/api-service.log
tail -f logs/worker-service.log
```

