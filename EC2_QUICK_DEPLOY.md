# 🚀 Deployment Rapid pe EC2

## Comenzi pentru EC2

### 1. Conectează-te la EC2
```bash
ssh -i your-key.pem ec2-user@your-ec2-ip
```

### 2. Navighează la directorul aplicației
```bash
cd /home/ec2-user/app/books-reporting
```

### 3. Pull ultimele modificări
```bash
git pull origin main
```

### 4. Rulează scriptul de deployment
```bash
chmod +x EC2_DEPLOYMENT.sh
./EC2_DEPLOYMENT.sh
```

## Sau manual (pas cu pas):

### Pasul 1: Pull codul
```bash
cd /home/ec2-user/app/books-reporting
git pull origin main
```

### Pasul 2: Activează venv și instalează dependențe
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Pasul 3: Verifică Redis
```bash
redis-cli ping
# Dacă nu rulează:
sudo systemctl start redis
# sau
redis-server --daemonize yes
```

### Pasul 4: Restart serviciul
```bash
sudo systemctl restart books-reporting
sudo systemctl status books-reporting
```

### Pasul 5: Verifică statusul
```bash
# Verifică scheduler-ul
curl http://localhost:5001/api/scheduler-status

# Vezi logurile
sudo journalctl -u books-reporting -f
```

## Configurație Finală

✅ **Scheduler**: 10:00 AM (ora României - Europe/Bucharest)
✅ **UK scraping**: Activ (detectare automată pentru `.co.uk`)
✅ **US scraping**: Activ (detectare automată pentru `amazon.com`)
✅ **Metoda screenshots**: Activ (OCR pentru extragere BSR când HTML parsing eșuează)

## Verificare Funcționare

### Verifică că scheduler-ul rulează:
```bash
curl http://localhost:5001/api/scheduler-status
```

Ar trebui să vezi:
```json
{
  "running": true,
  "jobs": [
    {
      "id": "daily_bsr_update",
      "name": "Daily BSR Update at 10:00 AM Bucharest time",
      "next_run": "2024-01-XX 10:00:00+02:00"
    }
  ]
}
```

### Verifică logurile:
```bash
sudo journalctl -u books-reporting -n 50
```

## Probleme Comune

### Service nu pornește:
```bash
# Verifică erorile
sudo journalctl -u books-reporting -n 100

# Verifică dacă portul este liber
sudo lsof -i :5001

# Verifică permisiunile
ls -la /home/ec2-user/app/books-reporting
```

### Redis nu rulează:
```bash
# Pornește Redis
sudo systemctl start redis
# sau
redis-server --daemonize yes

# Verifică
redis-cli ping
```

### Git pull eșuează:
```bash
# Verifică conexiunea
ping github.com

# Sau clonează manual
cd /home/ec2-user/app
rm -rf books-reporting
git clone your-repo-url books-reporting
```

## Test Manual Scraping

Pentru a testa manual scraping-ul:
```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate
python3 update_bsr.py
```

Aceasta va rula scraping-ul pentru toate cărțile (UK și US) și va actualiza Google Sheets.

