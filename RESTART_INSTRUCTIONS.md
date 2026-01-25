# 🔄 Instrucțiuni Restart Servicii

## Repornirea tuturor serviciilor

### Metoda 1: Script automat (Recomandat)
```bash
./restart_all_services.sh
```

### Metoda 2: Script simplu
```bash
./start_all.sh
```

## Ce face scriptul:

1. ✅ Oprește toate serviciile existente (FastAPI, Celery, Redis)
2. ✅ Curăță cache-ul Python
3. ✅ Pornește Redis (dacă nu rulează)
4. ✅ Pornește Celery Worker
5. ✅ Pornește FastAPI Server
6. ✅ Verifică statusul tuturor serviciilor

## Configurație Scheduler

**Scraping-ul rulează zilnic la: 10:00 AM (ora României - Europe/Bucharest)**

- Timezone: `Europe/Bucharest` (UTC+2/UTC+3 cu DST)
- Ora: `10:00` (exact)
- Configurat în: `app/main.py` și `config.py`

## Verificare Status

### Verifică dacă serviciile rulează:
```bash
# FastAPI
curl http://localhost:5001/api/scheduler-status

# Redis
redis-cli ping

# Celery
ps aux | grep celery
```

### Vezi logurile:
```bash
# FastAPI logs
tail -f logs/fastapi.log

# Celery logs
tail -f logs/celery-worker.log
```

## Probleme comune

### Redis nu pornește:
```bash
# Mac
brew services start redis

# Linux
sudo systemctl start redis
# sau
redis-server --daemonize yes
```

### Celery nu pornește:
Verifică dacă există `app/tasks/bsr_tasks.py` sau `services/worker-service/celery_app.py`

### FastAPI nu pornește:
Verifică dacă există `app/main.py` și că portul 5001 este liber:
```bash
lsof -i :5001
```

## Manual Restart (dacă scripturile nu funcționează)

```bash
# Oprește tot
pkill -f "uvicorn.*app.main:app"
pkill -f "celery.*worker"
pkill -f "redis-server"

# Pornește Redis
redis-server --daemonize yes

# Pornește Celery
celery -A app.tasks.bsr_tasks worker --loglevel=info --detach

# Pornește FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 5001
```

## Pe EC2/Server

Dacă rulezi pe un server, folosește:
```bash
./restart_service.sh  # pentru systemd service
```

Sau manual:
```bash
sudo systemctl restart books-reporting
sudo systemctl status books-reporting
```

