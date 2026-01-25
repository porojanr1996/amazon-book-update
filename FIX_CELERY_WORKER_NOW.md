# 🔧 Fix Celery Worker - Pas cu Pas

## Problema
- Git pull a eșuat (modificări locale)
- Celery Worker nu răspunde

## Soluție Rapidă

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# 1. Rezolvă conflictul git
git stash
git pull origin main
git stash pop  # Dacă vrei să păstrezi modificările locale, sau lasă-le stashed

# 2. Oprește toate worker-urile
pkill -f "celery.*worker"
sleep 3

# 3. Verifică că toate procesele sunt oprite
ps aux | grep celery | grep -v grep

# 4. Pornește worker-ul cu scriptul actualizat
chmod +x start_celery_worker_ec2.sh
./start_celery_worker_ec2.sh

# 5. Așteaptă 5 secunde
sleep 5

# 6. Verifică statusul
celery -A app.tasks.bsr_tasks inspect stats
celery -A app.tasks.bsr_tasks inspect registered
```

## Dacă worker-ul tot nu pornește

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate
mkdir -p logs

# Pornește manual cu toate opțiunile
celery -A app.tasks.bsr_tasks worker \
    --loglevel=info \
    --logfile=logs/celery-worker.log \
    --detach \
    --pidfile=logs/celery-worker.pid \
    -n "celery-worker-$(hostname)" \
    --concurrency=2

# Așteaptă 3 secunde
sleep 3

# Verifică
ps aux | grep celery
tail -n 20 logs/celery-worker.log
```

## Test Task

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

python3 << EOF
from app.tasks.bsr_tasks import update_all_worksheets_bsr
import time

print("Sending task...")
result = update_all_worksheets_bsr.delay()
print(f"Task ID: {result.id}")

time.sleep(5)
print(f"Task state: {result.state}")
EOF
```

