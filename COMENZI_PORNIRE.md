# 🚀 Comenzi pentru Pornirea Manuală a Serverului

## Opțiunea 1: Pornire Rapidă (Recomandat)

```bash
# Navighează în directorul proiectului
cd /Users/testing/books-reporting

# Activează virtual environment
source venv/bin/activate

# Verifică/pornește Redis
redis-cli ping || brew services start redis

# Pornește toate serviciile automat
./START_SIMPLE.sh
```

Sau:

```bash
./scripts/start_all_services.sh
```

---

## Opțiunea 2: Pornire Manuală Pas cu Pas

### Pasul 1: Pregătire

```bash
# Navighează în directorul proiectului
cd /Users/testing/books-reporting

# Activează virtual environment
source venv/bin/activate

# Verifică că Redis rulează
redis-cli ping
# Dacă nu rulează, pornește-l:
brew services start redis
```

### Pasul 2: Pornește Sheets Service (port 8001)

**Terminal 1:**
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/sheets-service
python3 main.py
```

Sau cu uvicorn:
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/sheets-service
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

### Pasul 3: Pornește Scraper Service (port 8002)

**Terminal 2:**
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/scraper-service
python3 main.py
```

Sau cu uvicorn:
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/scraper-service
python -m uvicorn main:app --host 0.0.0.0 --port 8002
```

### Pasul 4: Pornește API Service (port 5001) - Serverul Principal

**Terminal 3:**
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/api-service
python3 main.py
```

Sau cu uvicorn:
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/api-service
python -m uvicorn main:app --host 0.0.0.0 --port 5001
```

Sau direct din root:
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
python run_fastapi.py
```

### Pasul 5: Pornește Worker Service (Celery)

**Terminal 4:**
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
cd services/worker-service
celery -A celery_app worker --loglevel=info
```

---

## Opțiunea 3: Pornire în Background (cu logs)

### Pornește toate serviciile în background:

```bash
cd /Users/testing/books-reporting
source venv/bin/activate

# Sheets Service
cd services/sheets-service
python3 main.py > ../../logs/sheets-service.log 2>&1 &
cd ../..

# Scraper Service
cd services/scraper-service
python3 main.py > ../../logs/scraper-service.log 2>&1 &
cd ../..

# API Service
cd services/api-service
python3 main.py > ../../logs/api-service.log 2>&1 &
cd ../..

# Worker Service
cd services/worker-service
celery -A celery_app worker --loglevel=info > ../../logs/worker-service.log 2>&1 &
cd ../..
```

---

## Verificare Status

### Verifică că serviciile rulează:

```bash
# Verifică porturile
lsof -ti:8001  # Sheets Service
lsof -ti:8002  # Scraper Service
lsof -ti:5001  # API Service

# Health checks
curl http://localhost:8001/health  # Sheets
curl http://localhost:8002/health  # Scraper
curl http://localhost:5001/health  # API
```

### Deschide dashboard-ul:

```bash
open http://localhost:5001/
```

Sau deschide manual în browser: **http://localhost:5001/**

---

## Vizualizare Logs

```bash
# Logs live pentru fiecare serviciu
tail -f logs/sheets-service.log
tail -f logs/scraper-service.log
tail -f logs/api-service.log
tail -f logs/worker-service.log
```

---

## Oprire Servicii

### Oprește toate serviciile:

```bash
# Oprește serviciile pe porturi
lsof -ti:8001,8002,5001 | xargs kill

# Oprește Celery worker
pkill -f "celery.*celery_app"
```

### Sau oprește individual:

```bash
# Găsește PID-ul procesului
lsof -ti:5001  # pentru API Service
lsof -ti:8001  # pentru Sheets Service
lsof -ti:8002  # pentru Scraper Service

# Oprește procesul
kill <PID>
```

---

## Troubleshooting

### Redis nu rulează:
```bash
# Verifică status
redis-cli ping

# Pornește Redis
brew services start redis

# Sau manual
redis-server
```

### Port deja folosit:
```bash
# Găsește procesul care folosește portul
lsof -ti:5001

# Oprește procesul
lsof -ti:5001 | xargs kill
```

### Eroare "Module not found":
```bash
# Asigură-te că venv este activat
source venv/bin/activate

# Reinstalează dependențele
pip install -r requirements.txt
```

---

## Rezumat Rapid

**Cea mai simplă metodă:**
```bash
cd /Users/testing/books-reporting
source venv/bin/activate
./START_SIMPLE.sh
```

**Dashboard disponibil la:** http://localhost:5001/



