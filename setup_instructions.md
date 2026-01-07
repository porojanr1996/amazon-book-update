# Instrucțiuni de Setup Pas cu Pas

## Pasul 1: Instalare Python și Dependențe

```bash
# Verificați că aveți Python 3.8+
python3 --version

# Creați un virtual environment (recomandat)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# sau
venv\Scripts\activate  # Windows

# Instalați dependențele
pip install -r requirements.txt
```

## Pasul 2: Configurare Google Sheets API

### 2.1. Creați un proiect Google Cloud

1. Accesați [Google Cloud Console](https://console.cloud.google.com/)
2. Creați un proiect nou sau selectați unul existent
3. Notează numele proiectului

### 2.2. Activați API-urile necesare

1. Mergi la "APIs & Services" > "Library"
2. Caută și activează:
   - **Google Sheets API**
   - **Google Drive API**

### 2.3. Creați Service Account

1. Mergi la "APIs & Services" > "Credentials"
2. Click pe "Create Credentials" > "Service Account"
3. Completează:
   - Service account name: `bsr-scraper`
   - Service account ID: se generează automat
   - Click "Create and Continue"
4. Skip "Grant this service account access to project" (sau adaugă rol "Editor")
5. Click "Done"

### 2.4. Descărcați cheia JSON

1. Click pe Service Account-ul creat
2. Mergi la tab-ul "Keys"
3. Click "Add Key" > "Create new key"
4. Selectează "JSON"
5. Click "Create" - se va descărca un fișier JSON
6. Redenumește fișierul la `credentials.json` și mută-l în directorul proiectului

### 2.5. Partajați Google Sheet-ul

1. Deschideți Google Sheet-ul
2. Click pe butonul "Share" (Partajare)
3. Copiați email-ul Service Account din `credentials.json` (câmpul `client_email`)
4. Adăugați acest email cu permisiuni "Editor"
5. Click "Send"

## Pasul 3: Pregătire Google Sheet

### Structura Sheet-ului

Sheet-ul trebuie să aibă următoarea structură:

| Book Name | Author | Amazon Link | Category | 2024-01-01 | 2024-01-02 | ... |
|-----------|--------|-------------|----------|------------|------------|-----|
| Book 1    | Author 1 | https://... | Fiction US | 1234 | 1250 | ... |
| Book 2    | Author 2 | https://... | Fiction UK | 5678 | 5800 | ... |

**Important:**
- Prima linie trebuie să conțină header-ele
- Coloana D+ vor conține datele zilnice de BSR (se adaugă automat)
- Coloana "Category" este opțională dar recomandată pentru filtrare

### Obținere Spreadsheet ID

1. Deschideți Google Sheet-ul
2. Copiați ID-ul din URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
   ```
3. Salvați acest ID pentru configurare

## Pasul 4: Configurare Variabile de Mediu

1. Copiați `.env.example` la `.env`:
   ```bash
   cp .env.example .env
   ```

2. Editați `.env` cu valorile corecte:
   ```env
   GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
   GOOGLE_SHEETS_SPREADSHEET_ID=your_actual_spreadsheet_id_here
   SCHEDULE_TIME=10:00
   SCHEDULE_TIMEZONE=Europe/Bucharest
   ```

## Pasul 5: Testare

### Testare Scraper Manual

```bash
python daily_scraper.py
```

Ar trebui să vedeți:
- Conectare la Google Sheets
- Citire cărți
- Scraping BSR pentru fiecare carte
- Actualizare Google Sheets

### Testare Website

```bash
python app.py
```

Deschideți browser-ul la `http://localhost:5000` și verificați:
- Se încarcă dashboard-ul
- Se afișează graficele
- Se afișează clasamentele

## Pasul 6: Configurare Automatizare Zilnică

### Opțiunea A: Cron Job (Linux/Mac)

1. Deschideți crontab:
   ```bash
   crontab -e
   ```

2. Adăugați linia (ajustați path-urile):
   ```bash
   0 10 * * * cd /Users/testing/books-reporting && /usr/bin/python3 daily_scraper.py >> scraper.log 2>&1
   ```

3. Salvați și ieșiți

4. Verificați că cron rulează:
   ```bash
   crontab -l
   ```

### Opțiunea B: Systemd Timer (Linux)

Creați `/etc/systemd/system/bsr-scraper.service`:
```ini
[Unit]
Description=Amazon BSR Daily Scraper
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/books-reporting
ExecStart=/usr/bin/python3 /path/to/books-reporting/daily_scraper.py
Environment="PATH=/usr/bin:/usr/local/bin"
```

Creați `/etc/systemd/system/bsr-scraper.timer`:
```ini
[Unit]
Description=Run BSR scraper daily at 10:00 AM Bucharest time

[Timer]
OnCalendar=*-*-* 10:00:00
TimeZone=Europe/Bucharest
Persistent=true

[Install]
WantedBy=timers.target
```

Activează:
```bash
sudo systemctl enable bsr-scraper.timer
sudo systemctl start bsr-scraper.timer
sudo systemctl status bsr-scraper.timer
```

## Pasul 7: Deployment Website

### Folosind Gunicorn + Nginx

1. Instalați Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Creați un fișier `gunicorn_config.py`:
   ```python
   bind = "127.0.0.1:5000"
   workers = 4
   timeout = 120
   ```

3. Rulați cu Gunicorn:
   ```bash
   gunicorn -c gunicorn_config.py app:app
   ```

4. Configurare Nginx (exemplu):
   ```nginx
   server {
       listen 80;
       server_name ranks.novamediamarketing.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

5. Testați configurația Nginx:
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Folosind PM2

```bash
npm install -g pm2
pm2 start app.py --interpreter python3 --name bsr-dashboard
pm2 save
pm2 startup  # Urmează instrucțiunile pentru auto-start
```

## Verificare Finală

1. ✅ Scraper-ul rulează manual fără erori
2. ✅ Website-ul se încarcă și afișează date
3. ✅ Cron/Systemd timer este configurat
4. ✅ Log-urile se scriu corect în `scraper.log`
5. ✅ Datele se actualizează în Google Sheets

## Suport

Dacă întâmpinați probleme:
1. Verificați log-urile: `tail -f scraper.log`
2. Verificați că toate dependențele sunt instalate
3. Verificați că Google Sheets API este activat
4. Verificați că Service Account are acces la Sheet

