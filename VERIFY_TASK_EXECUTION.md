# ✅ Verificare Execuție Task Celery

## Status Actual

✅ **Celery Worker funcționează corect:**
- Conectat la Redis: `redis://localhost:6379/0`
- Task-uri înregistrate: `bsr.update_all_worksheets`, `bsr.update_worksheet`
- A procesat deja 2 task-uri `bsr.update_all_worksheets`

⚠️ **Problema:** Există 2 worker-uri cu același nume (DuplicateNodenameWarning)

## Soluție: Repornește cu un singur worker

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# 1. Oprește toate worker-urile existente
pkill -f "celery.*worker"
sleep 2

# 2. Verifică că toate procesele sunt oprite
ps aux | grep celery

# 3. Pornește un singur worker cu nume unic
mkdir -p logs
celery -A app.tasks.bsr_tasks worker \
    --loglevel=info \
    --logfile=logs/celery-worker.log \
    --detach \
    --pidfile=logs/celery-worker.pid \
    --concurrency=2 \
    -n "celery-worker-$(hostname)" \
    > /dev/null 2>&1

# 4. Așteaptă 3 secunde
sleep 3

# 5. Verifică statusul
celery -A app.tasks.bsr_tasks inspect stats
celery -A app.tasks.bsr_tasks inspect registered
```

## Test Task Execution

După ce ai repornit worker-ul, testează task-ul:

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

python3 << EOF
from app.tasks.bsr_tasks import update_all_worksheets_bsr
import time

print("Sending task...")
result = update_all_worksheets_bsr.delay()
print(f"Task ID: {result.id}")

# Așteaptă 10 secunde
print("Waiting 10 seconds for task to start...")
time.sleep(10)

# Verifică statusul
print(f"Task state: {result.state}")
print(f"Task ready: {result.ready()}")

# Verifică în Celery
from app.celery_app import celery_app
inspect = celery_app.control.inspect()
active = inspect.active()
print("\nActive tasks:", active)
EOF
```

## Monitorizare Loguri

În alt terminal, monitorizează logurile:

```bash
# FastAPI logs
sudo journalctl -u books-reporting -f | grep -E "(BSR|Celery|task|Task|Sending)"

# Celery Worker logs
tail -f logs/celery-worker.log | grep -E "(update_all_worksheets|Received task|Starting BSR|Task bsr)"
```

## Verificare Finală

După ce task-ul rulează, verifică:

1. **Logurile Celery Worker** - ar trebui să vezi:
   - `Received task: bsr.update_all_worksheets[...]`
   - `Starting BSR update task ... for all worksheets`
   - `Processing worksheet X/Y: ...`

2. **Logurile FastAPI** - ar trebui să vezi:
   - `Sending BSR update task to Celery...`
   - `BSR update task sent to Celery with ID: ...`

3. **Statusul task-ului** - ar trebui să treacă de la `PENDING` la `PROGRESS` și apoi la `SUCCESS`

