# Ghid de Deployment

## Opțiuni de Deployment

### 1. Deployment pe VPS (Recomandat)

#### Cerințe:
- VPS cu Ubuntu/Debian
- Python 3.8+
- Nginx (pentru reverse proxy)
- Domain name configurat

#### Pași:

1. **Conectare la server:**
```bash
ssh user@your-server.com
```

2. **Instalare dependențe sistem:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx git
```

3. **Clonează proiectul:**
```bash
cd /var/www
git clone <your-repo-url> books-reporting
cd books-reporting
```

4. **Setup Python environment:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

5. **Configurare variabile de mediu:**
```bash
cp env_template.txt .env
nano .env  # Editează valorile
```

6. **Upload credentials.json:**
```bash
# Folosește scp sau editor pentru a adăuga credentials.json
scp credentials.json user@server:/var/www/books-reporting/
```

7. **Testare:**
```bash
python test_setup.py
python daily_scraper.py  # Test manual
```

8. **Configurare Gunicorn:**
```bash
pip install gunicorn
```

Creează `/etc/systemd/system/bsr-dashboard.service`:
```ini
[Unit]
Description=BSR Dashboard Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/books-reporting
Environment="PATH=/var/www/books-reporting/venv/bin"
ExecStart=/var/www/books-reporting/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

9. **Activează serviciul:**
```bash
sudo systemctl enable bsr-dashboard
sudo systemctl start bsr-dashboard
sudo systemctl status bsr-dashboard
```

10. **Configurare Nginx:**
Creează `/etc/nginx/sites-available/bsr-dashboard`:
```nginx
server {
    listen 80;
    server_name ranks.novamediamarketing.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/books-reporting/static;
    }
}
```

Activează site-ul:
```bash
sudo ln -s /etc/nginx/sites-available/bsr-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

11. **Configurare SSL (Let's Encrypt):**
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ranks.novamediamarketing.com
```

12. **Configurare cron pentru scraping zilnic:**
```bash
crontab -e
```

Adaugă:
```bash
0 10 * * * cd /var/www/books-reporting && /var/www/books-reporting/venv/bin/python3 daily_scraper.py >> /var/www/books-reporting/scraper.log 2>&1
```

### 2. Deployment pe Google Cloud Run

1. **Creează Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
```

2. **Build și deploy:**
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/bsr-dashboard
gcloud run deploy bsr-dashboard --image gcr.io/PROJECT_ID/bsr-dashboard --platform managed --region europe-west1
```

3. **Configurare Cloud Scheduler pentru scraping:**
```bash
gcloud scheduler jobs create http bsr-scraper \
  --schedule="0 10 * * *" \
  --time-zone="Europe/Bucharest" \
  --uri="https://YOUR-CLOUD-RUN-URL/run-scraper" \
  --http-method=POST
```

### 3. Deployment pe Heroku

1. **Creează Procfile:**
```
web: gunicorn app:app
worker: python scheduler.py
```

2. **Deploy:**
```bash
heroku create bsr-dashboard
git push heroku main
heroku config:set GOOGLE_SHEETS_SPREADSHEET_ID=your_id
heroku config:set GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
# Upload credentials.json via Heroku dashboard
```

### 4. Deployment pe DigitalOcean App Platform

1. **Creează app.yaml:**
```yaml
name: bsr-dashboard
services:
- name: web
  source_dir: /
  github:
    repo: your-repo
    branch: main
  run_command: gunicorn --bind 0.0.0.0:8080 app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: GOOGLE_SHEETS_SPREADSHEET_ID
    value: your_id
  - key: FLASK_ENV
    value: production
```

## Monitoring și Maintenance

### Verificare log-uri

```bash
# Log-uri scraper
tail -f scraper.log

# Log-uri Flask/Gunicorn
sudo journalctl -u bsr-dashboard -f

# Log-uri cron
grep CRON /var/log/syslog
```

### Backup Google Sheets

Google Sheets are backup automat, dar poți exporta datele:
```bash
# Folosește Google Sheets API pentru export periodic
```

### Actualizare cod

```bash
cd /var/www/books-reporting
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bsr-dashboard
```

## Troubleshooting

### Website nu se încarcă
- Verifică că serviciul rulează: `sudo systemctl status bsr-dashboard`
- Verifică log-urile: `sudo journalctl -u bsr-dashboard -n 50`
- Verifică Nginx: `sudo nginx -t`

### Scraper nu rulează
- Verifică cron: `crontab -l`
- Verifică log-uri: `tail -f scraper.log`
- Testează manual: `python daily_scraper.py`

### Erori Google Sheets
- Verifică că Service Account are acces
- Verifică că Spreadsheet ID este corect
- Verifică că API-urile sunt activate

## Securitate

1. **Nu commit-ați credentials.json** - este în .gitignore
2. **Folosește HTTPS** - configurare SSL obligatorie
3. **Restricționează accesul** - poți adăuga autentificare basic în Nginx
4. **Monitorizează log-urile** - pentru activități suspecte
5. **Actualizează dependențele** - periodic pentru securitate

