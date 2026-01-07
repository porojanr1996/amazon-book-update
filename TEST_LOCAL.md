# Testare Locală - Ghid Pas cu Pas

## ✅ Pasul 1: Dependențe Instalate

Dependențele sunt deja instalate! ✓

## 📋 Pasul 2: Configurare Google Sheets

### 2.1. Spreadsheet ID

Din link-ul tău, Spreadsheet ID-ul este:
```
1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA
```

### 2.2. Creează fișierul .env

```bash
cd /Users/testing/books-reporting
cp env_template.txt .env
```

Editează `.env` și adaugă:
```env
GOOGLE_SHEETS_CREDENTIALS_PATH=credentials.json
GOOGLE_SHEETS_SPREADSHEET_ID=1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA
FLASK_ENV=development
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
SCHEDULE_TIME=10:00
SCHEDULE_TIMEZONE=Europe/Bucharest
AMAZON_DELAY_BETWEEN_REQUESTS=2
AMAZON_RETRY_ATTEMPTS=3
```

### 2.3. Obține credentials.json

1. Mergi la [Google Cloud Console](https://console.cloud.google.com/)
2. Creează un proiect nou sau selectează unul existent
3. Activează **Google Sheets API** și **Google Drive API**
4. Creează un **Service Account**:
   - Mergi la "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Nume: `bsr-scraper`
   - Click "Create and Continue" > "Done"
5. Descarcă cheia JSON:
   - Click pe Service Account-ul creat
   - Tab "Keys" > "Add Key" > "Create new key" > "JSON"
   - Salvează fișierul ca `credentials.json` în directorul proiectului
6. Partajează Google Sheet-ul:
   - Deschide Sheet-ul
   - Click "Share"
   - Adaugă email-ul Service Account (găsești în `credentials.json`, câmpul `client_email`)
   - Permisiuni: "Editor"

## 🧪 Pasul 3: Testare

### 3.1. Test Setup Complet

```bash
cd /Users/testing/books-reporting
source venv/bin/activate
python test_setup.py
```

Ar trebui să vezi:
- ✓ All imports successful
- ✓ Config loaded
- ✓ Credentials file is valid
- ✓ Successfully connected to Google Sheets
- ✓ Found X books

### 3.2. Test Scraping Manual (O Carte)

Creează un script de test simplu:

```bash
python -c "
from google_sheets_transposed import GoogleSheetsManager
import config

manager = GoogleSheetsManager(
    config.GOOGLE_SHEETS_CREDENTIALS_PATH,
    config.GOOGLE_SHEETS_SPREADSHEET_ID
)

books = manager.get_all_books()
print(f'Found {len(books)} books')
for book in books[:3]:  # Primele 3
    print(f\"- {book['name']} by {book['author']}\")
"
```

### 3.3. Test Scraping Complet

```bash
source venv/bin/activate
python daily_scraper.py
```

**Atenție:** Acest test va încerca să scrie în Google Sheet! Dacă vrei doar să testezi fără să scrii, poți modifica temporar codul.

### 3.4. Test Website

```bash
source venv/bin/activate
python app.py
```

Apoi deschide browser la: `http://localhost:5000`

Ar trebui să vezi:
- Dashboard cu grafice
- Top 50 rankings
- Filtre pentru categorii și timp

## 🔍 Verificare Structură Sheet

Sheet-ul tău are structura:
- **Rândul 1:** Nume cărți (coloane B, C, D, ...)
- **Rândul 2:** Autori
- **Rândul 3:** Link-uri Amazon
- **Rândul 4+:** Date cu valorile BSR

Codul a fost actualizat să funcționeze cu această structură transpusă!

## ⚠️ Note Importante

1. **Format Date:** Sheet-ul folosește format `M/D/YYYY` (ex: `1/15/2024`)
2. **Coloane Skip:** Cărțile marcate cu `>>>SKIP` sau `>>>STOP` sunt ignorate
3. **Coloana A:** Este pentru date, nu pentru cărți
4. **Prima Carte:** Începe de la coloana B

## 🐛 Troubleshooting

### Eroare: "Failed to connect to Google Sheets"
- Verifică că `credentials.json` există și este valid
- Verifică că Service Account are acces la Sheet
- Verifică că Spreadsheet ID este corect

### Eroare: "No books found"
- Verifică că Sheet-ul are cel puțin 3 rânduri
- Verifică că există cărți în coloanele B+
- Verifică că nu sunt marcate cu `>>>SKIP`

### Website nu se încarcă
- Verifică că Flask rulează: `python app.py`
- Verifică portul 5000 nu este ocupat
- Verifică log-urile pentru erori

## ✅ Checklist Final

- [ ] `.env` creat și configurat
- [ ] `credentials.json` în directorul proiectului
- [ ] Google Sheet partajat cu Service Account
- [ ] `test_setup.py` rulează fără erori
- [ ] Scraping manual funcționează
- [ ] Website se încarcă și afișează date

