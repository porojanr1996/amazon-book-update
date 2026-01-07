# Setup Rapid - Ghid Pas cu Pas

## 🚀 Pași Rapizi

### Pasul 1: Obține credentials.json (5-10 minute)

1. **Mergi la Google Cloud Console:**
   - https://console.cloud.google.com/
   - Login cu contul tău Google

2. **Creează un proiect:**
   - Click pe dropdown-ul de proiect (sus stânga)
   - Click "New Project"
   - Nume: `bsr-scraper` (sau orice nume vrei)
   - Click "Create"

3. **Activează API-urile:**
   - Mergi la "APIs & Services" > "Library"
   - Caută "Google Sheets API" > Click > "Enable"
   - Caută "Google Drive API" > Click > "Enable"

4. **Creează Service Account:**
   - Mergi la "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Service account name: `bsr-scraper`
   - Click "Create and Continue"
   - Skip "Grant access" (sau lasă default)
   - Click "Done"

5. **Descarcă cheia JSON:**
   - Click pe Service Account-ul creat (`bsr-scraper`)
   - Tab "Keys" > "Add Key" > "Create new key"
   - Selectează "JSON"
   - Click "Create" - se va descărca automat un fișier JSON
   - **IMPORTANT:** Redenumește fișierul la `credentials.json`
   - Mută-l în folderul `/Users/testing/books-reporting/`

6. **Partajează Google Sheet-ul:**
   - Deschide Sheet-ul: https://docs.google.com/spreadsheets/d/1-y5ly84oAV1GkhpLlD3MfvLZSi-5UThypHXsmch6RiA
   - Click butonul "Share" (Partajare)
   - Deschide `credentials.json` și copiază email-ul din câmpul `client_email` (ex: `bsr-scraper@proiect-123456.iam.gserviceaccount.com`)
   - Adaugă acest email în Share cu permisiuni "Editor"
   - Click "Send"

### Pasul 2: Verifică Setup-ul

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

### Pasul 3: Testează Scraping (Opțional - va scrie în Sheet!)

```bash
source venv/bin/activate
python daily_scraper.py
```

**Atenție:** Acest test va scrie date reale în Google Sheet! Dacă vrei doar să testezi fără să scrii, spune-mi și modific codul.

### Pasul 4: Testează Website

```bash
source venv/bin/activate
python app.py
```

Apoi deschide browser la: **http://localhost:5000**

Ar trebui să vezi dashboard-ul cu grafice și rankings!

---

## ✅ Checklist

- [ ] `.env` creat (deja făcut ✓)
- [ ] `credentials.json` în folderul proiectului
- [ ] Google Sheet partajat cu Service Account email
- [ ] `test_setup.py` rulează fără erori
- [ ] Website se încarcă la http://localhost:5000

---

## 🆘 Ajutor

Dacă întâmpini probleme:

1. **"credentials.json not found"**
   - Verifică că fișierul este în `/Users/testing/books-reporting/`
   - Verifică că se numește exact `credentials.json` (nu `credentials (1).json`)

2. **"Failed to connect to Google Sheets"**
   - Verifică că ai partajat Sheet-ul cu email-ul Service Account
   - Verifică că Spreadsheet ID este corect în `.env`

3. **"No books found"**
   - Verifică că Sheet-ul are structura corectă (rânduri 1-3 cu cărți)
   - Verifică că nu sunt marcate cu `>>>SKIP`

---

## 🎯 Următorii Pași După Setup

După ce totul funcționează local:

1. **Configurează cron job** pentru scraping automat zilnic:
   ```bash
   ./setup_cron.sh
   ```

2. **Deploy pe server** (când ești gata) - vezi `DEPLOYMENT.md`

---

**Gata! Urmează pașii de mai sus și totul ar trebui să funcționeze!** 🚀

