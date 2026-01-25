# 🔍 Verificare Task Celery

## Problema
Job-ul de test s-a executat la 18:51:51, dar nu văd loguri de la Celery Worker care să indice că task-ul a fost procesat.

## Verificări necesare

### 1. Verifică logurile Celery Worker
```bash
tail -f logs/celery-worker.log | grep -E "(update_all_worksheets|bsr.update_all_worksheets|Received task|Task)"
```

### 2. Verifică dacă task-ul a fost trimis la Redis
```bash
redis-cli
> KEYS celery*
> LLEN celery
> LRANGE celery 0 -1
```

### 3. Testează manual task-ul Celery
```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

python3 << EOF
from app.tasks.bsr_tasks import update_all_worksheets_bsr

# Testează task-ul direct
print("Testing Celery task...")
result = update_all_worksheets_bsr.delay()
print(f"Task ID: {result.id}")
print(f"Task state: {result.state}")
EOF
```

### 4. Verifică configurația Celery
```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

python3 << EOF
from app.celery_app import celery_app
print("Celery app:", celery_app)
print("Broker URL:", celery_app.conf.broker_url)
print("Result backend:", celery_app.conf.result_backend)
print("Registered tasks:", list(celery_app.tasks.keys()))
EOF
```

### 5. Verifică dacă Celery Worker vede task-ul
```bash
celery -A app.tasks.bsr_tasks inspect registered
```

## Posibile probleme

1. **Task-ul nu este trimis corect** - Lambda function poate să nu funcționeze corect în contextul scheduler-ului
2. **Celery Worker nu este conectat la același Redis** - Verifică configurația
3. **Task-ul nu este înregistrat** - Verifică dacă task-ul este înregistrat în Celery

## Soluție temporară

Dacă task-ul nu funcționează prin scheduler, poți testa direct:

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

python3 << EOF
from app.tasks.bsr_tasks import update_all_worksheets_bsr

# Trimite task-ul direct
result = update_all_worksheets_bsr.delay()
print(f"Task ID: {result.id}")
print("Waiting for result...")
try:
    task_result = result.get(timeout=300)  # 5 minute timeout
    print("Task completed:", task_result)
except Exception as e:
    print(f"Task failed: {e}")
EOF
```

