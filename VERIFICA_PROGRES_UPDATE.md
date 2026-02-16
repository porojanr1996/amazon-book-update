# 🔍 Verificare Progres Update BSR

## Comenzi pentru a verifica progresul

### 1. Verifică logurile în timp real

```bash
# Loguri FastAPI (toate mesajele)
sudo journalctl -u books-reporting -f | grep -E "(BSR|✅|❌|Extragere|extracted|completed)"

# Loguri Celery Worker (dacă folosești Celery)
tail -f logs/celery-worker.log | grep -E "(BSR|update|worksheet|completed|success)"
```

### 2. Verifică ultimele loguri (ultimele 100 linii)

```bash
sudo journalctl -u books-reporting -n 100 --no-pager | grep -E "(BSR|✅|❌|extracted|completed)"
```

### 3. Verifică dacă update-urile s-au terminat

```bash
# Verifică ultimele mesaje
sudo journalctl -u books-reporting -n 50 --no-pager | tail -20

# Caută mesaje de finalizare
sudo journalctl -u books-reporting --since "5 minutes ago" | grep -E "(completed|finalizat|succes|error)"
```

### 4. Verifică în Google Sheets

Deschide Google Sheets și verifică:
- Dacă există valori noi în coloana BSR pentru data de astăzi
- Dacă rândul pentru astăzi are date actualizate

### 5. Verifică statusul task-ului (dacă folosești Celery)

```bash
cd /home/ec2-user/app/books-reporting
source venv/bin/activate

# Verifică task-uri active
celery -A app.tasks.bsr_tasks inspect active

# Verifică task-uri rezolvate recent
celery -A app.tasks.bsr_tasks inspect reserved
```

## Ce să cauți în loguri

### ✅ Semne de succes:
- `✅ BSR extracted: #12345`
- `✅ Successfully updated BSR`
- `BSR extraction completed: 12345`
- `Processing completed`

### ❌ Semne de probleme:
- `❌ Nu s-a putut extrage BSR`
- `CAPTCHA detected`
- `Error fetching`
- `Timeout`
- `The future belongs to a different loop` (ar trebui să nu mai apară)

## Dacă update-urile rulează lent

Update-urile pot dura:
- **UK worksheet (16 cărți):** ~10-20 minute (cu delay-uri de 45-120s)
- **US worksheet (32 cărți):** ~20-40 minute (cu delay-uri de 45-120s)
- **Total:** ~30-60 minute pentru ambele

Asta este normal datorită delay-urilor pentru a evita blocările.

