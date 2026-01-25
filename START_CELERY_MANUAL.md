# ⚙️ Pornire Manuală Celery Worker pe EC2

## Problema
Celery Worker nu pornește automat. Pornește-l manual:

## Soluție Rapidă

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# Verifică Redis
redis-cli ping

# Pornește Celery Worker
celery -A app.tasks.bsr_tasks worker --loglevel=info --logfile=logs/celery-worker.log --detach
```

## Sau cu nohup (pentru a rula în background)

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# Creează logs directory
mkdir -p logs

# Pornește Celery Worker în background
nohup celery -A app.tasks.bsr_tasks worker \
    --loglevel=info \
    --logfile=logs/celery-worker.log \
    --detach \
    --pidfile=logs/celery-worker.pid &

# Verifică
ps aux | grep celery
```

## Verificare

```bash
# Verifică dacă rulează
ps aux | grep celery

# Vezi logurile
tail -f logs/celery-worker.log

# Verifică scheduler-ul
curl http://localhost:5001/api/scheduler-status
```

## Dacă Celery nu pornește

Verifică dacă Celery este instalat:
```bash
source venv/bin/activate
pip install celery redis
```

Verifică dacă există app/tasks/bsr_tasks.py:
```bash
ls -la app/tasks/bsr_tasks.py
```

