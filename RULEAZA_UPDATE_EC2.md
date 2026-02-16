# 🚀 Comenzi pentru Update BSR pe EC2

## Opțiunea 1: Update pentru UK și US (Recomandat)

```bash
# Conectează-te la EC2
ssh -i /path/to/your-key.pem ec2-user@51.20.76.150

# Navighează la proiect
cd /home/ec2-user/app/books-reporting

# Actualizează codul
git pull origin main

# Rulează update pentru UK și US
chmod +x trigger_update_uk_us.sh
./trigger_update_uk_us.sh
```

## Opțiunea 2: Update pentru TOATE worksheets (Celery)

```bash
# Pe EC2
cd /home/ec2-user/app/books-reporting
git pull origin main

# Rulează update pentru toate worksheets
chmod +x trigger_update_all_celery.sh
./trigger_update_all_celery.sh
```

## Opțiunea 3: Manual prin API (curl)

```bash
# Pe EC2
cd /home/ec2-user/app/books-reporting

# Update pentru UK
curl -X POST http://localhost:5001/api/trigger-bsr-update \
  -H "Content-Type: application/json" \
  -d '{"worksheet": "Crime Fiction - UK"}'

# Update pentru US
curl -X POST http://localhost:5001/api/trigger-bsr-update \
  -H "Content-Type: application/json" \
  -d '{"worksheet": "Crime Fiction - US"}'
```

## Monitorizare Progres

### Loguri FastAPI
```bash
sudo journalctl -u books-reporting -f
```

### Loguri Celery Worker
```bash
tail -f logs/celery-worker.log
```

### Verificare Status Task
```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# Verifică task-uri active
celery -A app.tasks.bsr_tasks inspect active

# Verifică task-uri programate
celery -A app.tasks.bsr_tasks inspect scheduled
```

## Verificare Finală

După ce update-urile rulează, verifică în Google Sheets că BSR-urile au fost actualizate.

