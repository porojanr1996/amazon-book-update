# Amazon BSR Tracking System

Sistem automatizat pentru urmărirea rank-ului cărților de pe Amazon, cu salvare în Google Sheets și afișare pe website.

## Flow General

```
Amazon → Google Sheets → Website
```

## Structura Proiectului

- `amazon_scraper.py` - Scraper pentru extragerea BSR-ului de pe Amazon
- `google_sheets.py` - Integrare cu Google Sheets pentru citire/scriere date
- `daily_scraper.py` - Script principal pentru scraping zilnic
- `scheduler.py` - Scheduler pentru rulare automată zilnică
- `app.py` - Aplicație Flask pentru website
- `config.py` - Configurație centralizată
- `templates/` - Template-uri HTML
- `static/` - CSS și JavaScript pentru frontend

## Instalare

### 1. Instalare dependențe

```bash
pip install -r requirements.txt
```

### 2. Configurare Google Sheets API

1. Creați un proiect în [Google Cloud Console](https://console.cloud.google.com/)
2. Activați Google Sheets API și Google Drive API
3. Creați un Service Account și descărcați fișierul JSON cu credențiale
4. Salvați fișierul ca `credentials.json` în directorul proiectului
5. Partajați Google Sheet-ul cu email-ul Service Account (găsiți în credentials.json)

### 3. Configurare Google Sheet

Sheet-ul trebuie să aibă următoarea structură:
- **Coloana A**: Book Name (numele cărții)
- **Coloana B**: Author (autorul)
- **Coloana C**: Amazon Link (link-ul către produsul Amazon)
- **Coloana D+**: Valorile zilnice de BSR (se adaugă automat)

Prima linie trebuie să conțină header-ele.

### 4. Instalare și pornire Redis

Redis este necesar pentru caching și background jobs (Celery):

```bash
# Instalare Redis (macOS)
brew install redis

# Pornire Redis ca serviciu (recomandat - pornește automat la login)
brew services start redis

# Verificare că Redis rulează
redis-cli ping
# Ar trebui să returneze: PONG
```

**Notă**: Redis este necesar pentru performanță optimă. Fără Redis, aplicația va funcționa dar caching-ul va fi dezactivat.

### 5. Configurare variabile de mediu

Copiați `.env.example` la `.env` și completați valorile:

```bash
cp .env.example .env
```

Editați `.env`:
```
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
SCHEDULE_TIME=10:00
SCHEDULE_TIMEZONE=Europe/Bucharest
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1
```

### 6. Obținere Spreadsheet ID

Spreadsheet ID-ul se găsește în URL-ul Google Sheet-ului:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
```

## Utilizare

### Rulare manuală scraping

```bash
python daily_scraper.py
```

### Rulare scheduler (pentru automatizare zilnică)

```bash
python scheduler.py
```

### Rulare website

```bash
python app.py
```

Website-ul va fi disponibil la `http://localhost:5000`

## Deployment

### Opțiunea 1: Cron Job (Linux/Mac)

Adăugați în crontab pentru rulare zilnică la 10:00 AM (Bucharest time):

```bash
crontab -e
```

Adăugați linia:
```
0 10 * * * cd /path/to/books-reporting && /usr/bin/python3 daily_scraper.py >> scraper.log 2>&1
```

### Opțiunea 2: Systemd Timer (Linux)

Creați un fișier `/etc/systemd/system/bsr-scraper.service`:

```ini
[Unit]
Description=Amazon BSR Daily Scraper
After=network.target

[Service]
Type=oneshot
User=your-user
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

Activează timer-ul:
```bash
sudo systemctl enable bsr-scraper.timer
sudo systemctl start bsr-scraper.timer
```

### Opțiunea 3: Cloud Scheduler (Google Cloud)

Folosiți Google Cloud Scheduler pentru a declanșa un Cloud Function sau Cloud Run job zilnic.

### Deployment Website

Pentru deployment pe subdomeniu (ex: `ranks.novamediamarketing.com`):

1. **Folosind Gunicorn**:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. **Configurare Nginx**:
```nginx
server {
    listen 80;
    server_name ranks.novamediamarketing.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Folosind PM2** (Node.js process manager pentru Python):
```bash
npm install -g pm2
pm2 start app.py --interpreter python3 --name bsr-dashboard
pm2 save
pm2 startup
```

## Funcționalități

### Website Dashboard

- **Grafice BSR**: Afișare evoluție BSR în timp
- **Filtre timp**: 7 zile, 30 zile, 90 zile, 1 an, all time
- **Top 50 Rankings**: Clasamentul cărților după BSR curent
- **Filtrare pe categorii**: Vizualizare date pentru categorii specifice
- **Hover pe grafice**: Afișare valori exacte la hover

### Automatizare

- Rulare zilnică automată la 10:00 AM (Bucharest time)
- Scraping BSR pentru toate cărțile din Google Sheets
- Actualizare automată a datelor în Google Sheets
- Recalculare automată a mediilor în Google Sheets

## Adăugare Cărți Noi

Pentru a adăuga o carte nouă, adăugați pur și simplu un rând nou în Google Sheet cu:
- Numele cărții
- Autorul
- Link-ul Amazon

Sistemul va prelua automat BSR-ul la următoarea rulare.

## Note Tehnice

- Scraper-ul folosește BeautifulSoup pentru parsing HTML
- Rate limiting: 2 secunde între request-uri (configurabil)
- Retry logic: 3 încercări pentru fiecare carte
- Logging: Toate operațiunile sunt loggate în `scraper.log`

## Troubleshooting

### Eroare: "Failed to connect to Google Sheets"
- Verificați că fișierul `credentials.json` există și este valid
- Verificați că Service Account-ul are acces la Sheet
- Verificați că Spreadsheet ID-ul este corect

### Eroare: "BSR not found on page"
- Amazon poate bloca request-urile dacă sunt prea multe
- Verificați că link-urile Amazon sunt valide
- Poate fi necesar să folosiți proxy-uri sau să creșteți delay-ul între request-uri

### Website nu se încarcă
- Verificați că Flask rulează: `python app.py`
- Verificați log-urile pentru erori
- Verificați că portul 5000 este deschis

## Estimări

### Fezabilitate
✅ **DA** - Sistemul este complet fezabil și implementat

### Timp de implementare
- Setup inițial: 2-4 ore
- Configurare Google Sheets API: 30 minute
- Deployment: 1-2 ore
- Testare și ajustări: 1-2 ore

**Total: 4-8 ore**

### Costuri

**Setup inițial:**
- Google Cloud Service Account: Gratuit
- Hosting website: Depinde de provider (ex: $5-20/lună pentru VPS)
- Domeniu: Dacă nu există deja, ~$10-15/an

**Mentenanță:**
- Monitoring: Recomandat să verificați log-urile săptămânal
- Actualizări: Dacă Amazon schimbă structura paginii, poate fi necesară actualizare scraper (~1-2 ore)
- Hosting: $5-20/lună pentru VPS sau hosting

## Suport

Pentru probleme sau întrebări, verificați log-urile în `scraper.log` sau contactați echipa de dezvoltare.

