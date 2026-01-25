# 🔧 Fix Redis Corrupted Tasks

## Problema
Eroarea `ValueError: Exception information must include the exception type` apare când Celery încearcă să citească rezultatul unui task vechi care are metadata coruptă în Redis.

## Soluție: Șterge task-urile vechi din Redis

```bash
# 1. Conectează-te la Redis
redis-cli

# 2. Verifică ce task-uri există
KEYS celery-task-meta-*

# 3. Șterge toate task-urile vechi (opțional - doar dacă nu mai ai nevoie de ele)
KEYS celery-task-meta-* | xargs redis-cli DEL

# SAU șterge doar task-ul problematic
redis-cli DEL celery-task-meta-ae143799-fce9-4265-a25c-2f3be6e4cdfc

# 4. Ieși din Redis
exit
```

## Soluție Alternativă: Ignoră eroarea în cod

Dacă vrei să testezi task-ul fără să ștergi task-urile vechi, poți folosi un try-except:

```python
from app.tasks.bsr_tasks import update_all_worksheets_bsr
import time

print("Sending task...")
result = update_all_worksheets_bsr.delay()
print(f"Task ID: {result.id}")

time.sleep(5)

try:
    print(f"Task state: {result.state}")
except ValueError as e:
    print(f"Error reading task state (corrupted old task): {e}")
    print("Task was sent successfully, check Celery Worker logs")
```

## Verificare Task Nou

După ce ștergi task-urile vechi, testează din nou:

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

python3 << EOF
from app.tasks.bsr_tasks import update_all_worksheets_bsr
import time

print("Sending new task...")
result = update_all_worksheets_bsr.delay()
print(f"Task ID: {result.id}")

time.sleep(10)

try:
    state = result.state
    print(f"Task state: {state}")
    if state == 'PROGRESS':
        print(f"Task progress: {result.info}")
    elif state == 'SUCCESS':
        print(f"Task completed: {result.result}")
    elif state == 'FAILURE':
        print(f"Task failed: {result.info}")
except ValueError as e:
    print(f"Error reading task state: {e}")
    print("Check Celery Worker logs for task execution")
EOF
```

## Monitorizare Loguri

În alt terminal, monitorizează logurile:

```bash
tail -f logs/celery-worker.log | grep -E "(Received task|Starting BSR|update_all_worksheets|Task bsr)"
```

