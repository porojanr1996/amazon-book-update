# Resurse Necesare - Lista Completă

## 🖥️ 1. Hardware/Server

### Opțiunea A: VPS/Server Dedicat (Recomandat pentru Producție)

**Cerințe minime:**
- **RAM:** 512 MB - 1 GB (suficient pentru scraping + website)
- **CPU:** 1 core (suficient pentru utilizare normală)
- **Storage:** 10-20 GB (pentru sistem, cod, log-uri)
- **Bandwidth:** 100 GB/lună (suficient pentru scraping + trafic website)

**Recomandat:**
- **RAM:** 1-2 GB (pentru performanță mai bună)
- **CPU:** 1-2 cores
- **Storage:** 20-50 GB
- **Bandwidth:** 200 GB/lună

**Provideri recomandați:**
- DigitalOcean Droplet: $6-12/lună
- Linode Nanode: $5-10/lună
- Vultr: $6-12/lună
- Hetzner: €4-8/lună

**OS recomandat:** Ubuntu 20.04/22.04 LTS sau Debian 11

### Opțiunea B: Computer Local (Doar pentru Testare)

**Cerințe:**
- Orice computer modern (Windows/Mac/Linux)
- 2 GB RAM disponibil
- 5 GB storage liber
- Conexiune internet stabilă

**Limitări:**
- Website accesibil doar local
- Trebuie să fie pornit 24/7 pentru scraping automat
- Nu recomandat pentru producție

### Opțiunea C: Cloud Platform (Cel mai Simplu)

**Google Cloud Run:**
- Pay-per-use (aproximativ $0-5/lună pentru utilizare normală)
- Scalare automată
- Nu necesită gestionare server

**Heroku:**
- $7-25/lună (plan basic)
- Gestionare completă automată

---

## 💻 2. Software și Dependențe

### Python și Pachete

**Python:** Versiunea 3.8 sau mai nouă

**Pachete Python (instalare automată cu `pip install -r requirements.txt`):**
- google-api-python-client
- google-auth-httplib2
- google-auth-oauthlib
- gspread
- beautifulsoup4
- requests
- selenium (opțional, pentru scraping mai avansat)
- flask
- flask-cors
- python-dotenv
- schedule
- pytz
- lxml
- fake-useragent

**Total:** ~50-100 MB spațiu pentru pachete Python

### Alte Software Necesare

**Pentru Server Linux:**
- Nginx (pentru reverse proxy) - `sudo apt install nginx`
- Cron (deja instalat pe majoritatea sistemelor)
- Git (pentru clonare cod) - `sudo apt install git`

**Pentru Development Local:**
- Git (opțional)
- Editor de cod (VS Code, PyCharm, etc.)

---

## 🔐 3. Conturi și Accesuri

### Google Account și Servicii

**1. Google Account (Gratuit)**
- Cont Google standard
- Acces la Google Sheets
- Acces la Google Cloud Console

**2. Google Cloud Project (Gratuit)**
- Creezi un proiect în Google Cloud Console
- Activezi Google Sheets API (gratuit)
- Activezi Google Drive API (gratuit)

**3. Service Account (Gratuit)**
- Creezi Service Account în Google Cloud
- Descărci fișier JSON cu credențiale
- Partajezi Google Sheet-ul cu email-ul Service Account

**Cost:** $0 (toate sunt gratuite până la limite generoase)

### Hosting/Server

**Dacă folosești VPS:**
- Cont la provider (DigitalOcean, Linode, etc.)
- Acces SSH la server
- Acces root/sudo pentru instalare pachete

**Dacă folosești Cloud Platform:**
- Cont la provider (Google Cloud, Heroku, etc.)
- Acces API pentru deployment

---

## 🌐 4. Domeniu și DNS (Opțional)

### Dacă vrei subdomeniu (ex: ranks.novamediamarketing.com)

**Necesită:**
- Domeniu existent (novamediamarketing.com)
- Acces la DNS settings
- Configurare A record sau CNAME

**Cost:** $0 (dacă ai deja domeniul)

**Dacă nu ai domeniu:**
- Cumpărare domeniu: ~$10-15/an
- Sau folosești IP direct (mai puțin profesional)

---

## 📊 5. Google Sheets

### Structură Sheet

**Necesită:**
- Google Sheet creat (gratuit)
- Structură corectă cu coloane:
  - Coloana A: Book Name
  - Coloana B: Author
  - Coloana C: Amazon Link
  - Coloana D+: Date zilnice BSR

**Limitări Google Sheets (gratuite):**
- 10 milioane celule per sheet (suficient pentru mii de cărți)
- 200 de foi per spreadsheet
- 5 milioane de celule per spreadsheet

**Pentru utilizare normală:** Totul este gratuit!

---

## 💰 6. Costuri Totale Estimate

### Scenariul Economic (Shared Hosting)

**Setup inițial:**
- Google Cloud: $0
- Google Sheets: $0
- Setup timp: 2-4 ore (timpul tău sau developer)

**Lunar:**
- Hosting: $3-5/lună
- Domeniu: $0 (dacă ai deja) sau $1-1.5/lună
- **Total: $3-6.5/lună**

### Scenariul Standard (VPS)

**Setup inițial:**
- Google Cloud: $0
- Google Sheets: $0
- VPS setup: $0 (doar timp)

**Lunar:**
- VPS: $6-12/lună
- Domeniu: $0 (dacă ai deja) sau $1-1.5/lună
- **Total: $6-13.5/lună**

### Scenariul Premium (Cloud Platform)

**Setup inițial:**
- Google Cloud: $0
- Google Sheets: $0

**Lunar:**
- Cloud Platform: $7-20/lună
- Domeniu: $0 (dacă ai deja) sau $1-1.5/lună
- **Total: $7-21.5/lună**

---

## 📋 7. Checklist Resurse

### Hardware/Server
- [ ] VPS/Server cu minim 512 MB RAM, 1 CPU, 10 GB storage
- [ ] SAU computer local pentru testare
- [ ] SAU cont cloud platform (Google Cloud Run, Heroku)

### Software
- [ ] Python 3.8+ instalat
- [ ] Acces la terminal/command line
- [ ] Git (opțional, pentru version control)
- [ ] Nginx (dacă folosești VPS pentru producție)

### Conturi
- [ ] Google Account
- [ ] Acces la Google Cloud Console
- [ ] Cont la provider hosting (dacă folosești VPS)
- [ ] Acces la DNS (dacă vrei subdomeniu)

### Configurare
- [ ] Google Cloud Project creat
- [ ] Google Sheets API activat
- [ ] Google Drive API activat
- [ ] Service Account creat
- [ ] Credențiale JSON descărcate
- [ ] Google Sheet creat și partajat cu Service Account

### Cod și Dependențe
- [ ] Cod proiect descărcat/clonat
- [ ] Dependențe Python instalate (`pip install -r requirements.txt`)
- [ ] Fișier `.env` configurat cu credențiale
- [ ] `credentials.json` în directorul proiectului

---

## 🎯 8. Resurse Minime vs Recomandate

### Setup Minimal (Funcțional, dar limitat)

**Hardware:**
- VPS cu 512 MB RAM, 1 CPU, 10 GB storage
- SAU computer local

**Software:**
- Python 3.8+
- Dependențe Python

**Conturi:**
- Google Account
- Google Cloud Project

**Cost:** $0-6/lună

**Limitări:**
- Poate fi mai lent cu multe cărți
- Website poate fi mai lent cu trafic mare

### Setup Recomandat (Performanță Bună)

**Hardware:**
- VPS cu 1-2 GB RAM, 1-2 CPU, 20-50 GB storage

**Software:**
- Python 3.9+
- Nginx pentru reverse proxy
- PM2 sau systemd pentru gestionare procese

**Conturi:**
- Google Account
- Google Cloud Project
- Cont VPS provider

**Cost:** $6-15/lună

**Avantaje:**
- Performanță bună
- Scalabil pentru creștere
- Website rapid și stabil

---

## 📊 9. Utilizare Resurse (Estimare)

### Scraping Zilnic (10:00 AM)

**Pentru 10-20 cărți:**
- Timp execuție: 1-3 minute
- Bandwidth: ~10-20 MB
- CPU: 5-10% (pe 1 core)
- RAM: ~100-200 MB

**Pentru 50-100 cărți:**
- Timp execuție: 5-15 minute
- Bandwidth: ~50-100 MB
- CPU: 10-20% (pe 1 core)
- RAM: ~200-400 MB

**Pentru 100+ cărți:**
- Timp execuție: 15-30 minute
- Bandwidth: ~100-200 MB
- CPU: 20-30% (pe 1 core)
- RAM: ~400-600 MB

### Website (24/7)

**Trafic mic (10-50 vizitatori/zi):**
- RAM: ~100-200 MB
- CPU: 1-5% (constant)
- Bandwidth: ~100-500 MB/lună

**Trafic mediu (50-200 vizitatori/zi):**
- RAM: ~200-400 MB
- CPU: 5-10% (constant)
- Bandwidth: ~500 MB - 2 GB/lună

**Trafic mare (200+ vizitatori/zi):**
- RAM: ~400-800 MB
- CPU: 10-20% (constant)
- Bandwidth: ~2-10 GB/lună

---

## ✅ Rezumat Rapid

### Ce Ai Nevoie Minim:

1. **Server/VPS:** $6-12/lună SAU computer local (gratuit, dar limitat)
2. **Google Account:** Gratuit
3. **Google Cloud Project:** Gratuit
4. **Python 3.8+:** Gratuit
5. **Dependențe Python:** Gratuit (instalare automată)
6. **Domeniu:** Opțional, $0 dacă ai deja

### Cost Total Minim: **$6-12/lună** (doar hosting)

### Timp Setup: **2-4 ore** (o singură dată)

---

## 🚀 Următorii Pași

1. **Alege provider hosting** (DigitalOcean, Linode, etc.)
2. **Creează cont Google Cloud** și activează API-urile
3. **Configurează Google Sheets** și Service Account
4. **Instalează dependențe** pe server
5. **Deploy cod** și configurează cron job
6. **Testează** că totul funcționează

**Totul este documentat în `setup_instructions.md` și `DEPLOYMENT.md`!** 📚

