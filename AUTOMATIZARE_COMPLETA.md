# Automatizare Completă - Ghid Pas cu Pas

## 🎯 Ce Vrei Să Obții

✅ **Scraping automat zilnic la 10:00 AM** - fără intervenție manuală  
✅ **Website se actualizează automat** - când Google Sheets se actualizează, website-ul arată datele noi  
✅ **Totul rulează în background** - nu trebuie să faci nimic manual

---

## 📋 Pasul 1: Setup Cron Job (Automatizare Scraping)

### Opțiunea A: Setup Automat (Recomandat) 🚀

```bash
# 1. Fă scriptul executabil
chmod +x setup_cron.sh

# 2. Rulează setup-ul
./setup_cron.sh
```

Gata! Cron job-ul este configurat automat.

### Opțiunea B: Setup Manual

```bash
# 1. Deschide crontab pentru editare
crontab -e

# 2. Adaugă această linie (ajustă path-ul la directorul tău):
0 10 * * * cd /Users/testing/books-reporting && /usr/bin/python3 daily_scraper.py >> /Users/testing/books-reporting/scraper.log 2>&1

# 3. Salvează și ieși (în nano: Ctrl+X, apoi Y, apoi Enter)
```

### Verificare Cron Job

```bash
# Vezi toate cron job-urile active
crontab -l

# Ar trebui să vezi ceva de genul:
# 0 10 * * * /Users/testing/books-reporting/cron_scraper.sh
```

---

## 🌐 Pasul 2: Website se Actualizează Automat

**Bune știri: Website-ul se actualizează AUTOMAT!** 🎉

### De ce?

1. **Scraping-ul scrie în Google Sheets** la ora 10:00 AM
2. **Website-ul citește din Google Sheets** când cineva accesează pagina
3. **Rezultat:** Website-ul arată automat datele noi fără să faci nimic!

### Cum Funcționează?

```
10:00 AM → Cron job rulează scraper-ul
         ↓
    Scraper scrie BSR în Google Sheets
         ↓
    Cineva accesează website-ul
         ↓
    Website citește datele din Google Sheets
         ↓
    Website afișează datele actualizate ✨
```

**Nu trebuie să faci nimic!** Website-ul citește mereu datele fresh din Google Sheets.

---

## 🔧 Pasul 3: Rulare Website în Background (24/7)

Pentru ca website-ul să fie accesibil tot timpul, trebuie să ruleze continuu.

### Opțiunea A: Folosind PM2 (Recomandat pentru Development)

```bash
# 1. Instalează PM2
npm install -g pm2

# 2. Pornește website-ul cu PM2
pm2 start app.py --name bsr-dashboard --interpreter python3

# 3. Salvează configurația pentru auto-start
pm2 save
pm2 startup
# (urmează instrucțiunile afișate)

# 4. Verifică status
pm2 status
pm2 logs bsr-dashboard
```

### Opțiunea B: Folosind systemd (Linux - Recomandat pentru Production)

Creează `/etc/systemd/system/bsr-dashboard.service`:

```ini
[Unit]
Description=BSR Dashboard Flask App
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/Users/testing/books-reporting
Environment="PATH=/Users/testing/books-reporting/venv/bin"
ExecStart=/Users/testing/books-reporting/venv/bin/python3 /Users/testing/books-reporting/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Apoi:
```bash
# Activează serviciul
sudo systemctl enable bsr-dashboard
sudo systemctl start bsr-dashboard

# Verifică status
sudo systemctl status bsr-dashboard

# Vezi log-uri
sudo journalctl -u bsr-dashboard -f
```

### Opțiunea C: Folosind screen/tmux (Simplu, dar nu auto-restart)

```bash
# Instalează screen (dacă nu ai)
# macOS: brew install screen
# Linux: sudo apt install screen

# Pornește sesiunea
screen -S bsr-dashboard

# În sesiunea screen, rulează:
cd /Users/testing/books-reporting
source venv/bin/activate
python app.py

# Ieși din screen: Ctrl+A apoi D
# Reintră în screen: screen -r bsr-dashboard
```

---

## ✅ Verificare că Totul Funcționează

### 1. Verifică Cron Job

```bash
# Vezi cron job-urile
crontab -l

# Simulează rulare manuală (pentru test)
cd /Users/testing/books-reporting
python daily_scraper.py
```

### 2. Verifică Website

```bash
# Deschide browser la:
http://localhost:5000

# Sau dacă e pe server:
http://your-server-ip:5000
# sau
http://ranks.novamediamarketing.com
```

### 3. Verifică Log-uri

```bash
# Log-uri scraping
tail -f scraper.log

# Log-uri website (dacă folosești PM2)
pm2 logs bsr-dashboard

# Log-uri website (dacă folosești systemd)
sudo journalctl -u bsr-dashboard -f
```

---

## 🎯 Rezumat - Ce Ai Nevoie

### Pentru Scraping Automat:
1. ✅ Cron job configurat (rulează `setup_cron.sh`)
2. ✅ Script `cron_scraper.sh` executabil
3. ✅ Python și dependențele instalate

### Pentru Website Automat:
1. ✅ Website rulează în background (PM2, systemd, sau screen)
2. ✅ Website citește din Google Sheets (automat)
3. ✅ Când scraping-ul scrie în Sheets, website-ul arată datele noi (automat)

**Nu trebuie să faci nimic manual după setup!** 🚀

---

## 🔍 Troubleshooting

### Cron Job Nu Rulează

```bash
# Verifică că cron rulează
ps aux | grep cron

# Verifică log-urile sistem
grep CRON /var/log/syslog  # Linux
grep CRON /var/log/system.log  # macOS

# Testează manual
./cron_scraper.sh
```

### Website Nu Se Actualizează

1. **Verifică că scraping-ul a scris în Google Sheets:**
   - Deschide Google Sheet-ul manual
   - Verifică că există valori noi pentru data de azi

2. **Verifică că website-ul rulează:**
   ```bash
   pm2 status  # sau
   sudo systemctl status bsr-dashboard
   ```

3. **Verifică log-urile pentru erori:**
   ```bash
   pm2 logs bsr-dashboard
   ```

4. **Refresh browser-ul** (Ctrl+F5 sau Cmd+Shift+R)

### Website Nu Rulează 24/7

- **PM2:** Verifică `pm2 startup` și `pm2 save`
- **systemd:** Verifică `sudo systemctl enable bsr-dashboard`
- **screen:** Nu auto-restart, trebuie să pornești manual dacă serverul se repornește

---

## 📝 Checklist Final

- [ ] Cron job configurat (`crontab -l` arată job-ul)
- [ ] Testat scraping manual (`python daily_scraper.py`)
- [ ] Website rulează în background (PM2/systemd/screen)
- [ ] Website accesibil (deschis în browser)
- [ ] Verificat log-uri (fără erori)
- [ ] Testat că datele se actualizează (scraping → Sheets → Website)

**După ce completezi checklist-ul, totul ar trebui să funcționeze automat!** ✨

